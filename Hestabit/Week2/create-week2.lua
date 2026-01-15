-- Configuration
local root_dir = "week-2"

-- ==========================================
-- CONTENT DEFINITIONS (Verbatim from PDF)
-- ==========================================

local day1_md = [[
# Week 2 — Frontend Fundamentals (HTML + CSS + JavaScript)

### 🎯 Objective:
Enable you to build responsive UI layouts and manipulate DOM with JavaScript using ES6 concepts.

### Week-2 Topics

**HTML**
* Semantic HTML5 structure
* `<header>` `<footer>` `<nav>` `<main>` `<section>` `<article>`
* Forms, validation, accessibility basics
* `<canvas>` & media (`video`, `audio`)

**CSS / Styling**
* CSS Selectors (attribute, sibling, nth-child)
* Box model, specificity, units (`rem`, `vw`, `vh`)
* Flexbox, Grid (2D layouts)
* Responsive design (mobile-first, media queries)
* Animations, transitions

**JavaScript (ES6+)**
* Variables `let` vs `const`
* Arrays/objects (`map`, `filter`, `reduce`)
* Arrow functions / destructuring / spread operator
* DOM manipulation
* Event listeners
* Modular JS: splitting code into functions/modules

---

# DAY 1 – HTML5 + Semantic Layout

### 🔹 Learning Outcomes:
* Understand page structure
* Master semantic tags and responsive layout scaffolding

### Topic & Activity Table

| Topic | Activity |
| :--- | :--- |
| **HTML Fundamentals** | tags / structure / metadata |
| **Semantic HTML5** | Build semantic layout (no `<div>` allowed) |
| **Forms & media** | Build form (input, select, validation) and embed media |
| **Accessibility** | ARIA labels, alt text, tab index |
| **Documentation** | Write README with learnings |

### ✏️ Exercise:
Build a *Blog Page* using only semantic HTML, no CSS.
**Image for reference:**
https://designhooks.com/wp-content/uploads/2020/05/full-template-551-stand-blog-scaled.jpg

### ✅ Deliverable: 
`blog.html`
]]

local day2_md = [[
# DAY 2 – CSS Layout Mastery (Flexbox + Grid)

### 🔹 Learning Outcomes:
* Modern responsive layout using Flexbox & CSS Grid

### Topic & Activity Table

| Topic | Activity |
| :--- | :--- |
| **CSS Selectors & Specificity** | selector challenges |
| **Flexbox** | Build navbar + hero section |
| **CSS Grid** | Product grid layout (2/3/4 col based on width) |
| **Responsive approach** | Convert desktop → mobile-first |

### ✏️ Exercise:
Replicate a **UI screenshot given by mentor** using Flex/Grid.
**Image for Reference:**
https://cdn.mos.cms.futurecdn.net/gnvkfwLFzB7yGtbTjzqURA.jpg

### ✅ Deliverable: 
`index.html` + `style.css` + screenshots of comparison
]]

local day3_md = [[
# DAY 3 – JavaScript ES6 + DOM Manipulation

### 🔹 Learning Outcomes:
* Modern JS (ES6) + manipulating DOM without frameworks

### Topic & Activity Table

| Topic | Activity |
| :--- | :--- |
| **Variables/functions** | `let`/`const`, arrow functions |
| **Arrays/objects** | `map`, `filter`, `reduce`, mini-challenges |
| **DOM manipulation** | build navbar toggle, dropdown, modal |
| **Event listeners** | build counter + key events |

### ✏️ Exercise:
Build an **interactive FAQ accordion** using JS (click to expand).
Reference:
https://codeconvey.com/wp-content/uploads/2020/02/responsive-accordion-pure-css.png.webp

### ✅ Deliverable: 
`/js-dom-practice/*`
]]

local day4_md = [[
# DAY 4 – JS Utilities + LocalStorage Mini-Project

### 🔹 Learning Outcomes:
* Modular JS functions
* LocalStorage persistence

### Topic & Activity Table

| Topic | Activity |
| :--- | :--- |
| **Debugging DevTools** | breakpoints, watch |
| **Custom JS utilities** | `debounce`, `throttle`, `groupBy` |
| **LocalStorage project** | Build Todo app (persist on refresh) |
| **Error handling** | try/catch + error boundary folder (`logs/errors.md`) |

### ✏️ Exercise:
Build **Todo App with LocalStorage persistence**
(Add → Edit → Delete → Persist after refresh)

### ✅ Deliverable: 
`todo-app/`
]]

local day5_md = [[
# DAY 5 – Capstone UI + JS Project

### 🔹 Learning Outcomes:
Combine everything from HTML + CSS + JS into a working UI

### Project: Build a mini “E-commerce product listing page”

**Requirements:**
* Use fetch API:
  `https://dummyjson.com/products`
* Display product cards (title, image, price)
* Search bar (filter products)
* Sort (high → low price)
* Mobile responsive layout

**Image for Reference:**
https://codehim.com/wp-content/uploads/2021/09/bootstrap-5-ecommerce-product-list-navbar-and-hover-effects.png

### Activity & Output Table

| Activity | Output |
| :--- | :--- |
| **Project setup** | folder + planning |
| **UI using HTML + CSS** | skeleton ready |
| **JS fetch + rendering + search** | functional UI |
| **Final touches/responsive/polish** | proper layout |

### ✅ Deliverables:
* Repo: `week2-frontend`
* Pages inside repo:
  * `/index.html`
  * `/products.html`
* README containing **screenshots + what you learned**
]]

-- ==========================================
-- FILE CREATION LOGIC
-- ==========================================

-- Table mapping keys to content
local week_plan = {
    ["day-1"] = day1_md,
    ["day-2"] = day2_md,
    ["day-3"] = day3_md,
    ["day-4"] = day4_md,
    ["day-5"] = day5_md
}

-- Function to create directories (OS agnostic for standard shells)
local function create_dir(path)
    local cmd
    if package.config:sub(1,1) == "\\" then
        -- Windows
        cmd = 'if not exist "' .. path .. '" mkdir "' .. path .. '"'
    else
        -- Unix/Linux/Mac
        cmd = 'mkdir -p "' .. path .. '"'
    end
    os.execute(cmd)
end

-- Function to write file
local function write_file(path, content)
    local file = io.open(path, "w")
    if file then
        file:write(content)
        file:close()
        print("Created: " .. path)
    else
        print("Error creating file: " .. path)
    end
end

print("Generatiing Week 2 Structure...")

-- Loop through keys 1 to 5 to maintain order, though pairs() is random
for i = 1, 5 do
    local day_key = "day-" .. i
    local content = week_plan[day_key]
    
    -- Structure: week-2 / day-x / day-x.md
    local dir_path = root_dir .. "/" .. day_key
    local file_path = dir_path .. "/" .. day_key .. ".md"
    
    create_dir(dir_path)
    write_file(file_path, content)
end

print("Complete.")
