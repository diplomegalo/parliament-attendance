DROP TABLE IF EXISTS minutes_text;
DROP TABLE IF EXISTS minutes;

CREATE TABLE IF NOT EXISTS minutes(
    id SERIAL PRIMARY KEY,
    ref CHAR(4) NOT NULL UNIQUE,
    date DATE NOT NULL,
    session VARCHAR(20) NOT NULL,
    url VARCHAR(255) NOT NULL UNIQUE,
    is_temporary BOOLEAN NOT NULL
);

CREATE TABLE IF NOT EXISTS minutes_text(
    id SERIAL PRIMARY KEY,
    minute_id INT NOT NULL,
    text_integral TEXT NOT NULL,
    FOREIGN KEY (minute_id) REFERENCES minutes(id) ON DELETE CASCADE,
    UNIQUE (minute_id)
);
