CREATE TABLE IF NOT EXISTS compte_rendu_integral(
    id SERIAL PRIMARY KEY,
    ref CHAR(4) NOT NULL UNIQUE,
    date DATE NOT NULL,
    session VARCHAR(20) NOT NULL,
    url VARCHAR(255) NOT NULL UNIQUE,
    text_integral TEXT NOT NULL
)