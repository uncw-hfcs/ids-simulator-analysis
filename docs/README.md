# Cry Wolf simulated events

This repository contains analysis scripts and the data set used in the Cry Wolf experiment. The data set consists of simulated Intrusion Detection System (IDS) alerts. 

Currently, the IDS alerts are all derived from an *impossible travel* scenario. Impossible travel alerts are triggered when a user authenticates from two geographic locations within a period where physical travel between the two locations is impossible, e.g., authentications from London and Moscow with a time between authentications of 30 minutes. Physical travel in this time frame is impossible, but the authentications may be legitimate through technical means such as a Virtual Private Network (VPN). 

The dataset contains both *true alarms* where the impossible travel alert warrants further investigation for potential malicious activity, and *false alarms* where the alert is not cause for concern. Each alert contains the following data:
- Cities of Authentication - The two geographic locations from which the IDS detected an authentication. 
- Number of Successful Logins - The number of successful authentications from each location in the past 24 hours.
- Number of Failed Logins - The number of failed logins from each location in the past 24 hours.
- Source Provider - The type of internet provider the authorizations came from at each location. Possible values are:
   - Telecom - traditional Internet Service Providers 
   - Mobile/cellular - wireless carriers
   - Hosting/server - hosted service providers, e.g., VPNs, web hosts, and cloud computing
- Time between Authentications - The shortest time between authentications from the two cities in the past 24 hours.  Reported in decimal hours. This the field that triggers an alarm in a real IDS.
- VPN Confidence - A percent likelihood that the user utilized a VPN.

There are two versions of the dataset: 

- [30 true alarms and 43 false alarms](https://github.com/uncw-hfcs/ids-simulator-analysis/blob/master/events/old/events_corrected.csv) - Used in the original Cry Wolf experiment
- [25 true alarms and 48 false alarms](https://raw.githubusercontent.com/uncw-hfcs/ids-simulator-analysis/master/events/events.csv)

The sets contain differences in the "time between authentications" field for five of the alerts.
