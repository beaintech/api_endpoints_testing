mock_leads = [
    {
        "id": 101,
        "title": "Mock Lead A",
        "value": {
            "amount": 3000,
            "currency": "EUR"
        },
        "owner_id": 1,
        "label_ids": ["label-aaa"],
        "person_id": 10,
        "organization_id": 100,
        "expected_close_date": "2025-01-10",
        "visible_to": "1",
        "was_seen": True,
        "add_time": "2025-01-01 10:00:00"
    },
    {
        "id": 102,
        "title": "Mock Lead B",
        "value": {
            "amount": 5000,
            "currency": "USD"
        },
        "owner_id": 2,
        "label_ids": ["label-bbb"],
        "person_id": 11,
        "organization_id": 101,
        "expected_close_date": "2025-02-01",
        "visible_to": "3",
        "was_seen": False,
        "add_time": "2025-01-02 15:30:00"
    }
]

next_lead_id = 103
