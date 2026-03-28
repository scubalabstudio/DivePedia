-- Light equipment master table
CREATE TABLE lights (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL UNIQUE,
    manufacturer VARCHAR(100) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Strobe equipment master table  
CREATE TABLE strobes (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL UNIQUE,
    manufacturer VARCHAR(100) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Accessory equipment master table
CREATE TABLE accessories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL UNIQUE,
    company VARCHAR(100) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX idx_lights_manufacturer ON lights(manufacturer);
CREATE INDEX idx_strobes_manufacturer ON strobes(manufacturer);
CREATE INDEX idx_accessories_company ON accessories(company);

-- Disable RLS for development
ALTER TABLE lights DISABLE ROW LEVEL SECURITY;
ALTER TABLE strobes DISABLE ROW LEVEL SECURITY;
ALTER TABLE accessories DISABLE ROW LEVEL SECURITY;