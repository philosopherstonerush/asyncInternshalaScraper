# ayncInternshalaScraper

A scraper made with python to asynchronously scrap internship offers from internshala.

# How to use?
1) Install python
2) Install pipenv
`pip install pipenv`
3) Run 
`pipenv install`
if there are no active virtual environments or
`pipenv sync` 
if active environments are present
4) Initialize path name constants found here, `constants.py`.
Like this
`C:\\path\to\where\you\want\the\csv\file\to\be\created`
5) Your internship offers are displayed in the browser with the nicegui framework.
6) Select the internships you have applied to and then select export CSV to store them. Make sure that csv file already exists with column headers ["id","internship_name","company", "stipend", "posted", "portal", "applied_date", "call_back"]
7) Execute main.py file as you would any other python file.