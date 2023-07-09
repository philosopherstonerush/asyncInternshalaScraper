import csv
import datetime
import aiohttp
import asyncio
from bs4 import BeautifulSoup
import pandas as pd
from nicegui import ui, app
import constants
import re

# Error count
metaDataNotAvailable = 0
responseDenied = 0

# Internship offers that I have already scraped
df = pd.read_csv(constants.FILE)
df_na = pd.read_csv(constants.FILE_NOT_APPLIED)
ids_already_scraped = df["id"].tolist()
ids_already_scraped.extend(df_na["id"].to_list())

# List of internship offers currently scraped
internships_offers = []

async def main():
    # Cannot update global scope variables inside a function
    global metaDataNotAvailable 
    global responseDenied

    limit = asyncio.Semaphore(constants.LIMIT) # Limits the number of threads created
    
    tasks = [] # list to store the task objects
    
    # These skills must be similar to the ones that appear on the URL
    skills_internshala = {"python", "django", "flutter", "flutter-development", "c-programming", "sql", "mysql", "bash", "java", "hibernate-java", "rust", "javascript", "javascript-development", "data-analytics", "data-science", "database-building", "embedded-systems", "arduino", "machine-learning", "artificial-intelligence-ai"}
    web_internshala = "https://internshala.com/internships/work-from-home-{}-internships-in-chennai/"
    
    for elem in skills_internshala:
        task = asyncio.create_task(scrape_em_internshala(web_internshala.format(elem), limit))
        tasks.append(task)
    
    await asyncio.gather(*tasks) # Wait for all the task objects to finish executing
    
    for elem in tasks:
        # separate the result of the task object from other info
        res = elem.result()
        for elem in res:
            if len(elem) == 6: # Removing error, I should replace it with logs
                if elem not in internships_offers:
                    internships_offers.append(elem)
            else:
                if elem["id"] == "MetaData":
                    metaDataNotAvailable = metaDataNotAvailable + 1
                else:
                    responseDenied = responseDenied + 1
    
    # Sorting
    internships_offers.sort(key=natural_keys,reverse=True)


# Pass in the url and  semaphore limit
async def scrape_em_internshala(url, limit): 
    async with limit:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    body = await resp.text()
                    soup = BeautifulSoup(body, 'html.parser')
                    all_meta = soup.find_all(class_="internship_meta")
                    result = [] # [{"position": etc}]
                    # Scrapping specific
                    if all_meta:
                        for elem in all_meta:
                            x = {}
                            name_internship = elem.find(class_="view_detail_button")
                            if name_internship:
                                x["position"] = name_internship.text
                            else:
                                x["position"] = "unknown"
                            company = elem.find(class_="link_display_like_text view_detail_button")
                            if company:
                                x["company"] = company.text.strip()
                            else:
                                x["company"] = "unknown"
                            sti = elem.find(class_="stipend")
                            if sti:
                                x["stipend"] = sti.text.strip()
                            else:
                                x["stipend"] = "0"
                            day = elem.find(class_="status status-small status-success")
                            if day:
                                x["posted"] = day.text.strip()
                            else:
                                x["posted"] = "unknown"
                            id = elem.parent['internshipid']
                            if int(id) in ids_already_scraped:
                                continue
                            x["id"] = id
                            link = elem.find(class_="view_detail_button")
                            x["link"] = "www.internshala.com" + link["href"]
                            result.append(x)
                    else:
                        result.append({"id": "MetaData"}) # meta data wasnt available 
                    return result
                else:
                    return [{"id": "response"}] # response got denied

def writeToCSV(rows, file): # File -> Constants.FILE or Constants.FILE_NOT_APPLIED
    with open(file, mode='a', encoding="utf-8") as final_file:
        field_names_final=["id", "internship_name", "company", "stipend", "posted", "portal", "applied_date", "call_back"]
        writer = csv.DictWriter(final_file, fieldnames=field_names_final)
        date = datetime.date.today()
        for elem in rows:
            writer.writerow({"id": elem["id"], "internship_name": elem["position"], "company": elem["company"], "stipend": elem["stipend"], "posted": elem["posted"], "portal": "internshala", "applied_date": date, "call_back": ""})
    # Notify that the operation is done
    ui.notify("Done", position="bottom")


# Gui part of nicegui
def displayGUI():
    columns = [
    {
        'name': 'id',
        'label': 'ID',
        'field': 'id'
    },
    {
        'name': 'posted',
        'label': 'Posted',
        'field': 'posted'
    },
    {
        'name': 'position',
        'label': 'Position',
        'field': 'position'
    },
    {
        'name': 'company',
        'label': 'Company',
        'field': 'company'
    },
    {
        'name': 'stipend',
        'label': 'Stipend',
        'field': 'stipend'
    },
    {
        'name': 'link',
        'label': 'Link',
        'field': 'link'
    }
    ]
    # rows is the list of dicts
    rows = internships_offers
    length = len(internships_offers)
    ui.label("Internships scraped: " + str(length))
    ui.label("MetaData wasnt available for : " + str(metaDataNotAvailable))
    ui.label("Response denied for: " + str(responseDenied))
    # selection allows you to have an instance variable called selected that gives you the dicts that are selected by the user
    table = ui.table(rows=rows, columns=columns, title="Internships", pagination=10, selection= "multiple", row_key= "id").classes("w-full")
    # Most of these callback functions are anonymous lambda functions
    ui.button("Export CSV", on_click=lambda :writeToCSV(table.selected, constants.FILE))
    ui.button("EXCLUDE", on_click=lambda: writeToCSV(table.selected, constants.FILE_NOT_APPLIED)).classes("danger")
    ui.button("shutdown", on_click=app.shutdown)
    ui.run(reload=False)

# Sorting implementation
def atoi(stipend):
    return int(stipend) if stipend.isdigit() else stipend

def natural_keys(text):
    '''
    internships.sort(key=natural_keys) sorts in human order
    http://nedbatchelder.com/blog/200712/human_sorting.html
    (See Toothy's implementation in the comments)
    '''
    try:
        return [ atoi(c) for c in re.split(r'(\d+)', text["stipend"]) ]
    except KeyError:
        print(text)

# async main function is run until all threads are completed 
loop = asyncio.get_event_loop()
loop.run_until_complete(main())
displayGUI()

    