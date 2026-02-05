INSERT INTO `USERS` (id, group_id, email, password_hash, name, google_uid, created_at, updated_at) VALUES
  (1, 1, 'alice@example.com', 'hashed-password-1', 'Alice', 'google-uid-alice', NOW(), NOW()),
  (2, 1, 'bob@example.com',   'hashed-password-2', 'Bob',   'google-uid-bob',   NOW(), NOW());

INSERT INTO `SHARE_GROUPS` (id, name, owner_user_id, created_at, updated_at) VALUES
  (1, 'Main Group', 1, NOW(), NOW());

INSERT INTO `CATEGORIES` (id, user_id, group_id, name, color, is_in_type, created_at, updated_at) VALUES
  (1, 1, 1, 'Food',       '#F97316', 0, NOW(), NOW()),
  (2, 1, 1, 'Transport',  '#3B82F6', 0, NOW(), NOW()),
  (3, 1, 1, 'Salary',     '#22C55E', 1, NOW(), NOW()),
  (4, 2, 1, 'Groceries',  '#F97316', 0, NOW(), NOW()),
  (5, 2, 1, 'Rent',       '#6366F1', 0, NOW(), NOW()),
  (6, 2, 1, 'Side Income','#14B8A6', 1, NOW(), NOW());

INSERT INTO `RECEIPTS` (id, user_id, group_id, image_url, taken_at, ocr_status, created_at) VALUES
  (1, 1, 1, 'https://example.com/receipts/1.jpg', '2025-01-10 12:10:00', 'done', NOW()),
  (2, 2, 1, 'https://example.com/receipts/2.jpg', '2025-01-11 18:30:00', 'done', NOW());

INSERT INTO `RECEIPT_ITEMS` (id, receipt_id, category_id, item_name, price, detection_date) VALUES
  (1, 1, 1, 'Ramen',      980, '2025-01-10'),
  (2, 1, 1, 'Tea',        180, '2025-01-10'),
  (3, 2, 4, 'Vegetables', 650, '2025-01-11'),
  (4, 2, 4, 'Milk',       220, '2025-01-11');

INSERT INTO `MONEY_FLOWS` (id, user_id, category_id, receipt_id, group_id, amount, expense_date, memo, created_at, updated_at) VALUES
  (1, 1, 1, 1,    1,  1160, '2025-01-10', 'Lunch',          NOW(), NOW()),
  (2, 1, 2, NULL, 1,   480, '2025-01-11', 'Train',          NOW(), NOW()),
  (3, 1, 3, NULL, 1, 250000, '2025-01-01', 'January salary', NOW(), NOW()),
  (4, 1, 1, NULL, 1,   760, '2025-01-15', 'Dinner',         NOW(), NOW()),
  (5, 1, 2, NULL, 1,   300, '2025-01-16', 'Bus',            NOW(), NOW()),
  (6, 2, 4, 2,    1,   870, '2025-01-11', 'Grocery store',  NOW(), NOW()),
  (7, 2, 5, NULL, 1, 78000, '2025-01-05', 'January rent',   NOW(), NOW()),
  (8, 2, 6, NULL, 1, 12000, '2025-01-12', 'Freelance',      NOW(), NOW()),
  (9, 2, 4, NULL, 1,   540, '2025-01-14', 'Snacks',         NOW(), NOW()),
  (10, 2, 4, NULL, 1,  320, '2025-01-16', 'Bread',          NOW(), NOW());
