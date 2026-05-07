# Yan-Yans Clinic Appointment System

## 🎯 Objective

Develop a simplified Clinic Appointment System with three roles:

* Admin
* Doctor/Staff (Employee)
* User (Patient)

The system must include login, booking, approval workflow, and role-based dashboards.

---

## 🧑‍💻 Technologies

* Backend: Python (Flask)
* Database: MySQL (phpMyAdmin)
* Frontend: HTML, CSS, Bootstrap (for layout)

---

## 🔐 Authentication System

### User Login

* Users can:

  * Login
  * Create Account (Register)
* After login → redirected to Appointment Booking Interface

---

### Doctor/Staff Login

* Switch button available on login page
* No password required
* Login using **Unique Employee Tag** (created by Admin)

---

### Admin Login

* Small link/button at bottom of login page
* Login using admin credentials

---

## 👤 USER (PATIENT) FEATURES

### After Login → Appointment Booking Interface (Step-Based UI)

Steps:

### 1. Service Selection

* User selects a service
* Services are created and managed by Admin

---

### 2. Doctor/Staff Selection

* Displays only doctors related to the selected service
* Doctor specialties are based on services they provide

---

### 3. Date & Time Selection

* User selects available date and time
* Only available slots (based on doctor's schedule) should be shown
* User can later request to edit appointment:

  * Goes to "My Appointments"
  * Submits edit request
  * Admin approves changes
  * Doctor is notified

---

### 4. Confirm Appointment

* User inputs personal information:

  * Name
  * Age
  * Gender
  * Contact Info
* Review appointment details before confirming

---

### After Confirmation

* Generate **E-Receipt**
* Contains:

  * Patient Name
  * Service
  * Doctor
  * Date & Time
  * Amount
  * Reference Number
  * Status: **Pending (Red Indicator)**

---

### Appointment Status

* Pending → Awaiting approval
* Approved → Confirmed by Admin/Doctor
* Cancelled → Declined

---

### User Dashboard

* "My Appointments"

  * View appointments
  * Request edit
  * Delete appointment

---

## 🩺 DOCTOR / STAFF FEATURES

### Access:

* Dashboard
* Appointments
* Profile

---

### Dashboard

* Calendar view of appointments

---

### Appointments

* View assigned appointments only
* Approve or Cancel appointments

---

### Profile

* Edit:

  * Personal Info
  * Services Offered
  * Availability Schedule
* View appointment history (logs)

---

## 🛠️ ADMIN FEATURES

### Full System Access

---

### Dashboard

* Calendar view of ALL appointments

---

### All Appointments

* View all appointments
* Approve / Cancel appointments
* Manage appointment requests (edit requests)

---

### Services Management

* Add services offered by the clinic
* These services appear in user booking interface

---

### Employees Management

* View all doctors/staff
* Create doctor accounts
* Generate **Unique Employee Tags** for login

---

## 🗄️ Database Structure

### Users Table

* id
* name
* email
* password
* role (user)

---

### Employees Table

* id
* name
* specialization
* employee_tag (for login)
* availability

---

### Services Table

* id
* service_name
* description
* price

---

### Appointments Table

* id
* user_id
* employee_id
* service_id
* date
* time
* status (Pending, Approved, Cancelled)
* reference_number

---

### Appointment Requests Table (Optional)

* id
* appointment_id
* requested_date
* requested_time
* status (Pending, Approved, Rejected)

---

## ⚙️ Core Features

* Role-based login system
* Step-by-step booking interface (Service → Doctor → Date & Time → Confirm)
* Dynamic doctor filtering based on service
* Appointment approval system
* E-receipt generation
* Calendar-based dashboards
* Employee tag login system (no password)

---

## 🚫 Simplifications

* No email/SMS notifications
* No payment gateway
* Basic UI only (focus on functionality)

---

## 📌 Important Notes

* Keep implementation SIMPLE and readable
* Follow exact booking flow (step-based UI)
* Do NOT include category selection (Service only)
* Use Flask routing and MySQL properly
* Ensure role-based redirection after login
* Ensure doctor filtering based on selected service
* Ensure appointment approval workflow is implemented
