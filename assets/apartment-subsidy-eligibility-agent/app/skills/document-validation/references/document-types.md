# Document Types Reference

| Document Type       | Accepted Formats               | Mandatory Fields                                      |
|---------------------|-------------------------------|-------------------------------------------------------|
| national_id         | Physical ID, e-ID scan        | name, dob, id_number, nationality, expiry, country    |
| passport            | Biometric, non-biometric scan | name, dob, passport_number, nationality, expiry, country |
| payslip             | PDF, image                    | name, net_income, currency, period, employer          |
| bank_statement      | PDF                           | name, account_balance, currency, period, bank_name    |
| residency_proof     | Utility bill, municipal cert  | name, address, issue_date, authority                  |
| tenancy_contract    | Signed PDF                    | landlord, tenant, address, start_date, end_date, rent |
