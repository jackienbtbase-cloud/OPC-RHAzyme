import os, requests
from requests.auth import HTTPBasicAuth
from supabase import create_client

JIRA_DOMAIN = os.getenv("JIRA_DOMAIN")
JIRA_EMAIL = os.getenv("JIRA_EMAIL")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

def sync_emulsion_tickets():
    url = f"https://{JIRA_DOMAIN}/rest/api/2/search/jql"
    payload = {
        "jql": 'project = "EMULSION"', # Update with exact project key
        "fields": ["*all"], # Required to grab custom fields
        "maxResults": 100
    }
    
    response = requests.post(url, json=payload, auth=HTTPBasicAuth(JIRA_EMAIL, JIRA_API_TOKEN))
    issues = response.json().get("issues", [])

    for issue in issues:
        fields = issue.get("fields", {})
        
        # Extract latest comment safely
        comments_array = fields.get("comment", {}).get("comments", [])
        latest_comment = "<i>No comments yet.</i>"
        if comments_array:
            raw_comment = comments_array[-1].get("body", "<i>No comments yet.</i>")
            latest_comment = raw_comment.replace("\n", "<br>")

        # Extract Item values safely (handling dropdown objects if necessary)
        item1_field = fields.get("customfield_XXXXX") # Item 1
        item1 = item1_field.get("value", "") if isinstance(item1_field, dict) else (item1_field or "")

        data = {
            "issue_key": issue["key"],
            "summary": fields.get("summary", ""),
            "assignee": fields.get("assignee", {}).get("displayName", "Unassigned") if fields.get("assignee") else "Unassigned",
            "status": fields.get("status", {}).get("name", ""),
            "customer": fields.get("customfield_XXXX1", ""), # Replace with Customer ID
            "destination": fields.get("customfield_XXXX2", ""), # Replace with Destination ID
            "item_1": item1,
            "qty_1": int(fields.get("customfield_XXXX3") or 0), # Replace with Qty 1 ID
            # Add customfield parsing for item_2, qty_2, item_3, qty_3 here...
            "po_link": fields.get("customfield_XXXX4", ""), # Replace with PO Google Drive Link ID
            "do_link": fields.get("customfield_XXXX5", ""),
            "invoice_link": fields.get("customfield_XXXX6", ""),
            "bc_bl_link": fields.get("customfield_XXXX7", ""),
            "latest_comment": latest_comment,
            "updated_at": fields.get("updated")
        }
        supabase.table("emulsion_tickets").upsert(data).execute()

if __name__ == "__main__":
    sync_emulsion_tickets()