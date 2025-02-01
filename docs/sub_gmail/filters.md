## Gmail Filters

Gmail filters are rules that automatically organize emails based on search criteria. They can be used to: 
- Archive emails 
- Delete emails
- Star emails
- Apply labels to emails
- Mark emails as spam
- Forward emails

## Gmail Filters for Email Cleanup


### 1. Retaining Starred and Important Emails Forever

### **Filter Criteria:**

- Ensures starred and important emails are never deleted.

 ### **Gmail Filter Setup:**

1. Go to **Gmail Settings** → **Filters and Blocked Addresses** → **Create a new filter**.
2. Enter the following message in Has_words:
   ```
   is:important OR is:starred
   ```
3. Click **Create filter**.
4. Check the box for **Never send it to Spam**.
5. Check the box for **Never delete it**.
   - if there is no option create a label for it.
   - 
6. Click **Create filter**.

---

### 2. Automatically Deleting Spam Emails

### **Filter Criteria:**

- Deletes existing spam emails and incoming spams.

### **Gmail Filter Setup:**

1. Go to **Gmail Settings** → **Filters and Blocked Addresses** → **Create a new filter**.
2. Enter the following message in include_the_words:
   ```
   is:spam
   ```
3. Click **Create filter**.
4. Check the box for **Delete it**.
5. Check **Also apply filter to matching conversations** - To apply for existing spam emails
6. Click **Create filter**.

---

### 3. Deleting Emails Older Than 1 Year 

### **Filter Criteria:**

- Emails older than **365 days**
- Excludes **starred** and **important** emails 

### **Gmail Filter Setup:**

1. Go to **Gmail Settings** → **Filters and Blocked Addresses** → **Create a new filter**.
2. Enter the following message in Has_words:
   ```
   older_than:365d -is:important -is:starred
   ```
   - -is:important : excludes important emails from deletion
   - -is:starred : excludes starred emails from deletion
  
3. Click **Create filter**.
4. Check the box for **Delete it**.
5. Check **Also apply filter to matching conversations** - To apply for existing emails 
6. Click **Create filter**.



## **Verification & Testing**
- Check the **Trash folder** after creating filters to confirm emails are being moved correctly.
- Check the **Spam folder** after creating spam filter to ensure spam emails are deleted.
- Ensure important and starred emails remain untouched by checking in their fields.

---

