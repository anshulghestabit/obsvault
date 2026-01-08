

script 1 eek autom 

-- create_structure.lua
-- Creates directories: week-1 to week-8, each with day-1 to day-5

local function mkdir(path)
    -- Cross-platform directory creation
    local command
    if package.config:sub(1,1) == "\\" then
        -- Windows
        command = 'mkdir "' .. path .. '" 2>nul'
    else
        -- Linux / macOS
        command = 'mkdir -p "' .. path .. '"'
    end
    os.execute(command)
end

for week = 1, 8 do
    local week_dir = "week-" .. week
    mkdir(week_dir)

    for day = 1, 5 do
        local day_dir = week_dir .. "/day-" .. day
        mkdir(day_dir)
    end
end

print("✅ Week and day directory structure created successfully.")
