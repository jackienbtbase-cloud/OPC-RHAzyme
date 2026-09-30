import os
import requests
from requests.auth import HTTPBasicAuth
from supabase import create_client, Client

JIRA_DOMAIN = os.getenv("JIRA_DOMAIN")
JIRA_EMAIL = os.getenv("JIRA_EMAIL")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

def sync_opc_rhazyme_tickets():
    url = f"https://{JIRA_DOMAIN}/rest/api/2/search/jql"
    
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    # Pagination control variables
    next_page_token = None
    max_results = 100
    target_limit = 500
    total_synced = 0
    
    print(f"Connecting to Jira via POST: {url}")
    
    while total_synced < target_limit:
        payload = {
            "jql": 'project = "NOR"',  # 改为 OPC & RHAzyme 的项目 Key
            "fields": ["*all"], 
            "maxResults": max_results
        }
        
        if next_page_token:
            payload["nextPageToken"] = next_page_token
            
        response = requests.post(url, headers=headers, json=payload, auth=HTTPBasicAuth(JIRA_EMAIL, JIRA_API_TOKEN))
        
        if not response.ok:
            print(f"Jira API Error {response.status_code}: {response.text}")
            break
            
        jira_data = response.json()
        issues = jira_data.get("issues", [])
        
        if len(issues) == 0:
            if total_synced == 0:
                print("Raw Jira Response:", jira_data)
            break

        for issue in issues:
            fields = issue.get("fields", {})
            key = issue["key"]
            
            comments_array = fields.get("comment", {}).get("comments", [])
            latest_comment = "<i>No comments yet.</i>"
            if comments_array:
                raw_comment = comments_array[-1].get("body", "<i>No comments yet.</i>")
                latest_comment = raw_comment.replace("\n", "<br>")

            def get_item_val(field_id):
                val = fields.get(field_id)
                return val.get("value", "") if isinstance(val, dict) else (val or "")

            data = {
                "issue_key": key,
                "summary": fields.get("summary", ""),
                "assignee": fields.get("assignee", {}).get("displayName", "Unassigned") if fields.get("assignee") else "Unassigned",
                "status": fields.get("status", {}).get("name", ""),
                "customer": fields.get("customfield_10282", ""),   # 对应新项目 Customer 字段[cite: 16]
                "destination": fields.get("customfield_10283", ""),# 对应新项目 Destination 字段[cite: 16]
                "item_1": get_item_val("customfield_10287"),      # Item 1[cite: 17]
                "qty_1": int(fields.get("customfield_10288") or 0),# Qty 1[cite: 18]
                "item_2": get_item_val("customfield_10289"),      # Item 2[cite: 17]
                "qty_2": int(fields.get("customfield_10290") or 0),# Qty 2[cite: 18]
                "item_3": get_item_val("customfield_10291"),      # Item 3[cite: 17]
                "qty_3": int(fields.get("customfield_10292") or 0),# Qty 3[cite: 18]
                "po_link": fields.get("customfield_10281", ""),    # PO Google Drive Link[cite: 17]
                "do_link": fields.get("customfield_10294", ""),    # DO Google Drive Link[cite: 17]
                "invoice_link": fields.get("customfield_10296", ""),# INV Google Drive Link[cite: 17]
                "bc_bl_link": fields.get("customfield_10337", ""),  # Vessel BC Google Drive Link[cite: 18]
                "latest_comment": latest_comment,
                "updated_at": fields.get("updated")
            }
            
            # 写入你刚才在 Supabase 新建的表
            supabase.table("opc_rhazyme_tickets").upsert(data).execute()
            print(f"Synced Ticket: {key}")
            total_synced += 1
            
            if total_synced >= target_limit:
                break

        next_page_token = jira_data.get("nextPageToken")
        
        if not next_page_token:
            break

    print(f"Database sync complete. Total synced: {total_synced}")

if __name__ == "__main__":
    sync_opc_rhazyme_tickets()
