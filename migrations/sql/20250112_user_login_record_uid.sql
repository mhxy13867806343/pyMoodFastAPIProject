-- 1. 添加新的 user_uid 列
ALTER TABLE user_login_record ADD COLUMN user_uid VARCHAR(28);

-- 2. 更新 user_uid 列的值
UPDATE user_login_record lr
JOIN user_inputs u ON lr.user_id = u.id
SET lr.user_uid = u.uid;

-- 3. 将 user_uid 列设为非空
ALTER TABLE user_login_record MODIFY COLUMN user_uid VARCHAR(28) NOT NULL;

-- 4. 添加外键约束
ALTER TABLE user_login_record ADD CONSTRAINT fk_user_login_record_user_uid
FOREIGN KEY (user_uid) REFERENCES user_inputs(uid);

-- 5. 删除旧的 user_id 列及其外键
ALTER TABLE user_login_record DROP FOREIGN KEY user_login_record_ibfk_1;
ALTER TABLE user_login_record DROP COLUMN user_id;
