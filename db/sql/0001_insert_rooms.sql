-- Insert Rooms
INSERT INTO Rooms (room_id, room_name, room_count, room_type, capacity, holiday_price_per_night, weekday_price_per_night, extra_bed_number, description, room_status) VALUES
  ('太', '太陽', 1, 'standard_family_room', 4, 3600, 3000, 1, '四人套房，實木床底', 'available'),
  ('月', '月亮', 1, 'economic_family_room', 2, 3400, 2800, 1, '四人雅房，實木床底，浴室在房門外左邊', 'available'),
  ('藍', '藍莓', 1, 'standard_double_room', 2, 2800, 2200, 1, '獨立露台', 'available'),
  ('紅', '紅莓', 1, 'standard_double_room', 2, 2800, 2200, 1, '獨立露台', 'available'),
  ('森', '森林', 1, 'standard_double_room', 2, 2800, 2200, 1, '獨立露台、實木地板、加大雙人床', 'available'),
  ('稻', '稻香', 1, 'standard_double_room', 2, 2800, 2200, 1, '獨立露台、閣樓床型', 'available'),
  ('天', '天空', 1, 'standard_double_room', 2, 2800, 2200, 1, '大型玻璃窗、窗邊景觀靠台', 'available'),
  ('星', '星空', 6, 'backpacker_bed', 1, 900, 900, 0, '上下鋪、各床獨立簾幕', 'available'),
  ('和', '和室', 1, 'washitsu', 4, 3600, 3600, 0, '隱藏房型', 'available'),
  ('草', '草地', 10, 'grass', 2, 1200, 1000, 2, '草地露營，附戶外廁所/淋浴間、水電', 'available');
