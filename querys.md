# User admin

INSERT INTO users (email, password, name) 
VALUES (
    'admin@example.com', 
    'pbkdf2:sha256:600000$abcd1234$e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
    'Admin'
);

