# Week 3: Advance Frontend (Next.js + TailwindCSS)

### Objective:
Train interns to build modern, production-grade frontends using:
* Next.js fundamentals (App Router / Pages / Routing / Layouts / Image optimization / SSR vs CSR basics)
* TailwindCSS (utility-first design + responsive components + reusable design system)

### Week-3 Topics

**Next.js Fundamentals**
* File-based routing
* `app/` directory structure (Next 15+)
* Layouts & nested layouts
* Page navigation (`Link`, `useRouter`)
* Static vs client components (`"use client"`)
* Image optimization (`next/image`)
* Fonts optimization (`next/font`)
* Metadata & SEO tags (`<Head />` or `metadata` config)

**TailwindCSS Fundamentals + Design System**
* Utility-first styling
* Responsive design (`sm`, `md`, `lg`, `xl`)
* Flexbox + Grid using Tailwind
* Spacing system (`p-x`, `m-x`, `gap-x`)
* Typography system
* Custom theme config in `tailwind.config.js`
* Component composition mindset (atoms → molecules → sections → pages)

**Component Architecture + UI Thinking**
* Reusable component system

**Folder structure:**
```text
/components
/app
/styles
```
---

# DAY 1 — TailwindCSS + UI System Basics

### Topics:
* Install Tailwind in Next.js
* Utility classes, spacing, colors, fonts
* Custom theme configuration

### Exercise:
Build a **Dashboard Layout skeleton** (header + sidebar)
**Image for reference (Create header and Sidebar only):**
https://assets.startbootstrap.com/img/meta/products/twitter/twitter-image-sb-admin.png

### Output:
* `/app/layout.jsx`
* `/components/ui/Navbar.jsx`
* `/components/ui/Sidebar.jsx`
