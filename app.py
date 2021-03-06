# import libraries
import requests
import csv
from bs4 import BeautifulSoup
import calendar
from datetime import time, datetime, timezone
import pandas as pd
import numpy as np

months = [name for name in list(calendar.month_name) if name != '']

# download the webpage
page = requests.get("https://en.wikipedia.org/wiki/2019_in_spaceflight#Orbital_launches")

# BS object
soup = BeautifulSoup(page.text, 'html.parser')

# extract the table under Orbital Launches 
table = soup.find_all("table",{"class":"wikitable collapsible"})[0] 

# get all the rows
table_rows = table.find_all('tr')

# All rows in one list
all_tds = [] 
for tr in table_rows: 
	td = tr.find_all('td') 
	row = [i.text.replace("\n","") for i in td] 
	all_tds.append(row) 
	#print(row)

# Ignoring the table headings
all_tds = all_tds[3:]

# payloads 
all_payloads = []


isMonth = False 	 								# is the row displaying month or payload/launch information
isLaunch = False 									# is the row displaying launch information
isPayload = False 									# is the row displaying payload information 
num_launches = 0 									# total number of launches
num_payloads = 0									# total number of payloads
currMonth = "NA" 									# launch month
curr_date = ""										# launch date	
rocket_name = ""									# name of the rocket associated with the payload

for td in all_tds:
	try: 
		if len(td) == 1 or len(td) == 2: 			# to extract month
			for s in td: 
				idx1 = s.find("edit") 
				idx2 = s.find(chr(8594)) 
				if idx1 != -1: 
					m = s[0:idx1-1] 
					if m in months: 
						isMonth = True 
						currMonth = m 
					if idx2 != -1: 
						m = s[s.find(chr(8594))+1:idx1-1] 
						if m in months: 
							isMonth = True 
							currMonth = m 

		else: 
			isMonth = False 
			#print("Data ",td,len(td),isMonth,currMonth) 

		if not isMonth: 
			if len(td) == 5: 
				isLaunch = True
				launch = td
				rocket_name = launch[1]
				launch_date = launch[0][0:launch[0].find('[')]
				year = 2019
				day = int(launch_date.split(" ")[0])
				month = -1

				hours = 0
				minutes = 0
				seconds = 0 
				mstr = ""
				for m in months: 
					if m in launch_date:  
						month = months.index(m)+1 
						mstr = m

				time = launch_date[launch_date.find(mstr)+len(mstr):]
				
				if len(time.split(":")) == 1:
					hours = 0
					minutes = 0
					seconds = 0
				else:
					hours = int(time.split(":")[0])
					minutes = int(time.split(":")[1])

					if len(time.split(":")) == 2:
						seconds = 0
					else:
						seconds = int(time.split(":")[2])
				
				# launch date in ISO format
				curr_date = datetime(year, month, day, hours, minutes, seconds, tzinfo=timezone.utc).isoformat()
				num_launches += 1 
				
			
			if len(td) == 6: 
				isPayload = True 
				outcome = td[5]
				payload_name = td[0]
				
				# includes rocket names of whose atleast one payload's outcome is either Successful, Operational or En route
				if outcome in ["Successful","Operational","En route"]:
					payload = [curr_date,rocket_name,payload_name,outcome]
					all_payloads.append(payload)
				num_payloads += 1 

	except Exception as e:

		pass		

# DataFrame of payloads and rocket names
all_payloads = pd.DataFrame(all_payloads,columns=["LaunchDate","RocketName","PayloadName","Outcome"])
all_payloads["Date"] = all_payloads.apply(lambda row: row["LaunchDate"][0:10],axis=1)
# Get distinct count of number of launches per day
final_count = pd.DataFrame(all_payloads["RocketName"].groupby(all_payloads["Date"]).unique()).reset_index()
final_count["Num_Launches"] = final_count.apply(lambda row: len(row["RocketName"]),axis=1) 
final_count["Date"] = pd.to_datetime(final_count["Date"])

# Initialise dataframe with all dates of the year 2019 and number of launches equal to zero
date_range = pd.Series(pd.date_range(start ='1-1-2019',end ='31-12-2019'))
date_range = pd.concat([date_range,pd.Series(np.zeros(dtype="int",shape=len(date_range)))],axis=1)
date_range.columns = ["LDate","Num_Launches"]
date_range["LaunchDate"] = pd.Series([x.isoformat() for x in date_range["LDate"]])

# Merge final_count with date_range (Left Outer Join) which gives all the dates and number of launches per date 
df = date_range.merge(final_count[["Date","Num_Launches"]],left_on="LDate",right_on="Date",how="left")
df["Num_Launches"] = df["Num_Launches_y"].fillna(0).astype(int)
df = df[["LaunchDate","Num_Launches"]] 

# Save the dataframe to csv
df.columns = ["date","value"]
df.to_csv("output.csv",index=False) 