from google.ads.googlcustomer_id=9820928751eads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException
from google.oauth2 import service_account
import os
from dotenv import load_dotenv,find_dotenv
import pandas as pd
import json
import pandas_gbq

load_dotenv(find_dotenv(usecwd=True), override=True)

#Unset environment variables for google ads client library
os.environ.pop("GOOGLE_ADS_CONFIGURATION_FILE_PATH", None)
#Read .env file and set environment variables
GOOGLE_ADS_DEVELOPER_TOKEN =os.getenv("GOOGLE_ADS_DEVELOPER_TOKEN")

GOOGLE_ADS_CLIENT_ID = os.getenv("GOOGLE_ADS_CLIENT_ID")
    
GOOGLE_ADS_CLIENT_SECRET = os.getenv("GOOGLE_ADS_CLIENT_SECRET")
GOOGLE_ADS_REFRESH_TOKEN = os.getenv("GOOGLE_ADS_REFRESH_TOKEN")
GOOGLE_ADS_LOGIN_CUSTOMER_ID = os.getenv("GOOGLE_ADS_LOGIN_CUSTOMER_ID")


# Configure the Google Ads client
config= {
    "developer_token": GOOGLE_ADS_DEVELOPER_TOKEN,
    "login_customer_id": GOOGLE_ADS_LOGIN_CUSTOMER_ID,
    "use_proto_plus":True,
    "client_id": GOOGLE_ADS_CLIENT_ID,
    "client_secret": GOOGLE_ADS_CLIENT_SECRET,
    "refresh_token": GOOGLE_ADS_REFRESH_TOKEN
    }



client = GoogleAdsClient.load_from_dict(config)


#Call the customer service
list_customers_request=client.get_service("CustomerService").list_accessible_customers()
print(type(list_customers_request))
resource_names=list(list_customers_request.resource_names)
records=[
  {"customer_resource_name": rn, "customer_id": rn.split("/")[-1]}
  for rn in resource_names
]

print(type(records))
df=pd.DataFrame(records)
print(df)


#Add the customer id and pull all the accounts listed inside it.



#Write a query to pull all the accounts inside the customer id



ga_service=client.get_service("GoogleAdsService")
query=f"""
    SELECT customer_client.client_customer,
     customer_client.currency_code,
      customer_client.descriptive_name,
       customer_client.level, 
       customer_client.id,
        customer_client.status,
         customer_client.time_zone, 
         customer_client.manager,
          customer_client.resource_name 
    FROM customer_client WHERE customer_client.level >= 1 
    ORDER BY customer_client.descriptive_name DESC
    """


response=ga_service.search_stream(customer_id=str(customer_id), query=query)
records=[]
for chunk in response:
    for row in chunk.results:
        customer_client=row.customer_client
        records.append(
            {
                "descriptive_name":customer_client.descriptive_name,
                "currency_code":customer_client.currency_code,
                
                "level":customer_client.level,
                "id":customer_client.id,
                "status":customer_client.status.name,
                "time_zone":customer_client.time_zone,
                "manager":customer_client.manager,
                

            }
        )
df=pd.DataFrame(records)


#df head
# print(df.head())
print(df.shape)
print(df.info())

#pull campaign inventory for each account id in the dataframe

ga_service=client.get_service("GoogleAdsService")
query=f"""
SELECT campaign.name,
 campaign_budget.amount_micros,
  campaign_budget.status, 
  campaign_budget.total_amount_micros,
  campaign.id, 
  FROM campaign
  WHERE customer.status = 'ENABLED'
  ORDER BY campaign.name
  """
campaign_records=GoogleAdsService.search_stream(customer_id=customer_client.id, query=query)
for chunk in campaign_records:
    for row in chunk.results:

        campaign_id=row.campaign.id
        campaign_name=row.campaign.name
        campaign_budget_amount_micros=row.campaign_budget.amount_micros
        campaign_budget_status=row.campaign_budget.status.name
        campaign_budget_total_amount_micros=row.campaign_budget.total_amount_micros
        records.append(
            {
                "customer_id":customer_client.id,
                "descriptive_name":customer_client.descriptive_name,
                "currency_code":customer_client.currency_code,
                "level":customer_client.level,
                "id":customer_client.id,
                "status":customer_client.status.name,
                "time_zone":customer_client.time_zone,
                "manager":customer_client.manager,
                "campaign_id":campaign_id,
                "campaign_name":campaign_name,
                "campaign_budget_amount_micros":campaign_budget_amount_micros,
                "campaign_budget_status":campaign_budget_status,
                "campaign_budget_total_amount_micros":campaign_budget_total_amount_micros
            }
        )
df=pd.DataFrame(records)
print(df.shape)
print(df.info())

    
        
        






#LOad bigquery credentials
GOOGLE_CLOUD_PROJECT_ID=os.getenv("GOOGLE_CLOUD_PROJECT_ID")
BIGQUERY_DATASET=os.getenv("BIGQUERY_DATASET")
BIGQUERY_TABLE=os.getenv("BIGQUERY_TABLE")
BIGQUERY_CREDENTIALS=os.getenv("BIGQUERY_CREDENTIALS")


#load df to bigquery table using pandas gbq
credentials=service_account.Credentials.from_service_account_file('./googleads.json'),
print("Credentials loaded", credentials)

pandas_gbq.to_gbq(
    df,
    f"{BIGQUERY_DATASET}.{BIGQUERY_TABLE}",
    project_id=GOOGLE_CLOUD_PROJECT_ID,
    if_exists="replace",
    credentials=credentials[0])


print("Data loaded to bigquery table")
print(f"Table {BIGQUERY_TABLE} in dataset {BIGQUERY_DATASET} in project {GOOGLE_CLOUD_PROJECT_ID}")




    


