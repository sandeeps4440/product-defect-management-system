# DefectTrack Pro — Product Defect Management System

A full Django web app where customers report product defects, admin reviews and assigns to the right team, and each role gets a **separate dashboard**.

---

## Quick Start (3 steps)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Setup DB + seed demo data (run once)
python setup.py

# 3. Start the server
python manage.py runserver
```

Then visit: **http://127.0.0.1:8000/**

---

## Demo Accounts

| Username        | Password     | Role            | Dashboard                        |
|-----------------|--------------|-----------------|----------------------------------|
| `admin`         | `admin123`   | Admin           | Control centre, assign complaints|
| `dev_alice`     | `staff123`   | Developer       | My assigned bugs/perf issues     |
| `designer_cara` | `staff123`   | Designer        | My assigned UI/UX issues         |
| `tester_dan`    | `staff123`   | Tester          | My assigned functionality tests  |
| `qa_emma`       | `staff123`   | QA Engineer     | My assigned security/compat      |
| `pm_frank`      | `staff123`   | Product Manager | My assigned physical damage      |
| `support_grace` | `staff123`   | Support Agent   | My assigned doc errors           |
| `customer1`     | `customer123`| Customer        | My reported complaints           |
| `customer2`     | `customer123`| Customer        | My reported complaints           |

> You can also **Register** your own account at `/register/`

---

## How It Works

```
Customer submits complaint  →  Status: "Pending Review"
        ↓
Admin reviews & assigns     →  Status: "Assigned"  (chooses team member)
        ↓
Staff works on it           →  Status: "In Progress"
        ↓
Staff resolves              →  Status: "Resolved"
        ↓
Admin closes                →  Status: "Closed"
```

**Admin always sees ALL complaints. Staff only see what's assigned to them. Customers only see their own.**

---

## Auto-Assignment Suggestions

When admin assigns, the system suggests the right team based on defect category:

| Defect Category         | Suggested Role     |
|-------------------------|--------------------|
| 🐛 Software Bug         | Developer          |
| 🎨 UI/UX Issue          | Designer           |
| ⚙️ Functionality Failure| Tester             |
| ⚡ Performance Issue    | Developer          |
| 🔒 Security Vulnerability| QA Engineer       |
| 📦 Physical Damage      | Product Manager    |
| 📄 Documentation Error  | Support Agent      |
| 🔌 Compatibility Issue  | QA Engineer        |

---

## Role-Based Dashboards

- **Customer** — See your complaints, track status, report new defects (with photo)
- **Admin** — See ALL complaints, pending review queue, assign to staff, full control
- **Developer/Designer/Tester/QA/PM/Support** — See only complaints assigned to them, update status

---

## Key Features

- ✅ Photo upload **required** when reporting a defect
- ✅ Complaints go to admin first (Pending Review)
- ✅ Admin assigns to specific staff member
- ✅ Each role sees a completely different dashboard
- ✅ Full activity timeline on each complaint
- ✅ Filter & search complaints
- ✅ Analytics with progress bars
- ✅ Register your own account

---

## Project Structure

```
defect_mgmt_v4/
├── core/               # Django config (settings, urls)
├── complaints/         # Main app
│   ├── models.py       # UserProfile, DefectCategory, Complaint, ComplaintUpdate
│   ├── views.py        # Role-based dashboard routing
│   ├── forms.py        # ComplaintForm (image required), AssignComplaintForm
│   ├── admin.py
│   ├── context_processors.py
│   ├── migrations/
│   ├── management/commands/seed_data.py
│   └── templates/complaints/
│       ├── base.html
│       ├── login.html
│       ├── register.html
│       ├── dashboard_customer.html   ← Customer dashboard
│       ├── dashboard_admin.html      ← Admin dashboard
│       ├── dashboard_staff.html      ← Developer/Designer/Tester/etc dashboard
│       ├── raise_complaint.html      ← Photo upload required
│       ├── complaint_list.html
│       ├── complaint_detail.html     ← Admin assign panel + staff update
│       ├── analytics.html
│       └── profile.html
├── manage.py
├── setup.py            ← Run this once to setup everything
└── requirements.txt
```
