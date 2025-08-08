# Transport Management Web App

## Overview

This is a modular Flask web application for managing transportation logistics, including company records, agreements, lorry details, routes, and letter records. It uses SQLite via SQLAlchemy and Jinja2 for templating.

---

## ✅ Current Status

- **Flask App** is modular, split into `app.py`, `routes/`, `models.py`
- **UI** is built with Bootstrap 5 and rendered using `dashboard.html`
- **Database** is SQLite (`transport/database.db`)
- **Modal-based editing** implemented for Lorry entries

---

## 📁 Project Structure

```
transport/
├── app.py
├── __init__.py
├── models.py
├── database.db          # ✅ Actual DB is located here
├── routes/
│   └── admin.py
├── templates/
│   └── dashboard.html
```

---

## 🧠 Model Summary

### `Company`
- id, name, address, phone, email

### `Agreement`
- FK to Company
- loa_number, total_mt_km, rate_per_mt_km, is_active

### `LorryDetails`
- capacity, carrier_size, remarks, number_of_wheels

### `Route`
- name, total_km
- Relationship: `stops` → List of `RouteStop`

### `RouteStop`
- route_id, location, type (enum), order, authority_id (FK)

### `LocationAuthority`
- location, authority

### `LetterRecord`
- lorry_id, route_id, booking_unit, is_home_depot, load_at_home, far_end_action, remarks

---

## ✅ Features Implemented

- Multi-tab Admin Dashboard (Company, Agreement, Lorry, Route Builder)
- Modal-based Edit for Lorry entries
- Agreement activation with toggle
- DB reset via CLI (`flask reset-db`)

---

## 🔜 In Progress / Next Steps

1. **Route Builder UI** (Google Maps-style)
   - Inputs for `from`, `to`, intermediate stops
   - Selectable `type`, `authority` per stop
2. **Admin.py Updates**
   - Handle route stop creation with full metadata
3. **More CRUD Modals**
   - Company, Agreement, Route edit modals
4. **UI Enhancements**
   - Client-side validation, error messages, status feedback

---

## 💾 Notes for Migration

To continue development on another system or under a paid ChatGPT account:
- Copy entire `/transport` folder
- Launch with: `flask --app transport.app run`
- Use virtual environment and install from `requirements.txt`

---

## 🧠 Assistant Instructions for Continuation

When resuming this project, the assistant should:
- Read and load all the above context
- Focus next on finalizing the Route Builder interface and backend logic in `admin.py`
- Avoid repeating what's done unless requested explicitly