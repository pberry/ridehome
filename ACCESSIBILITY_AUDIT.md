# Accessibility Audit Report

**Site:** The Ride Home - Link Archive
**Audit Date:** December 23, 2024
**WCAG Target:** WCAG 2.1 Level AA
**Auditor:** Automated analysis + manual review

---

## Executive Summary

The site demonstrates **good foundational accessibility** with semantic HTML, proper ARIA usage, and descriptive content. However, there are **critical color contrast issues** that prevent WCAG AA compliance for normal-sized text.

**Overall Grade:** B- (Needs Improvement)

**Critical Issues:** 2
**Moderate Issues:** 3
**Minor Issues:** 2

---

## 1. Color Contrast (WCAG 1.4.3) ❌ CRITICAL

### Solarized Light Theme

| Element | Colors | Ratio | WCAG AA | Status |
|---------|--------|-------|---------|--------|
| Body text | #657b83 on #fdf6e3 | 4.13:1 | **FAIL** | ❌ |
| Headings | #586e75 on #fdf6e3 | 4.99:1 | PASS | ✓ |
| Links | #268bd2 on #fdf6e3 | 3.41:1 | **FAIL** | ❌ |
| Visited links | #6c71c4 on #fdf6e3 | 4.06:1 | **FAIL** | ❌ |

**Required:** 4.5:1 for normal text (16px), 3:1 for large text (18.66px+)

### Solarized Dark Theme

| Element | Colors | Ratio | WCAG AA | Status |
|---------|--------|-------|---------|--------|
| Body text | #839496 on #002b36 | 4.75:1 | PASS | ✓ |
| Headings | #93a1a1 on #002b36 | 5.61:1 | PASS | ✓ |
| Links | #268bd2 on #002b36 | 4.08:1 | **FAIL** | ❌ |
| Visited links | #6c71c4 on #002b36 | 3.43:1 | **FAIL** | ❌ |

### Impact
- **Severity:** Critical
- **Users Affected:** All sighted users, especially those with low vision or color blindness
- **WCAG Level:** AA (fails), AAA (fails)

### Recommendation
**Increase contrast for links and light theme body text:**

```scss
// Light theme - darken text colors
$base00: #556873;  // Body text (currently #657b83) → 5.0:1
$base01: #485e6a;  // Headings (currently #586e75) → 6.2:1
$blue:   #1c6fa0;  // Links (currently #268bd2) → 4.8:1
$violet: #5858a8;  // Visited (currently #6c71c4) → 4.6:1

// Dark theme - lighten link colors
$blue:   #3ca0e6;  // Links (currently #268bd2) → 4.9:1
$violet: #8989d8;  // Visited (currently #6c71c4) → 4.6:1
```

**Alternative:** Increase font size to 18px (currently 16px) to meet large text threshold (3:1 ratio).

---

## 2. Empty Page Heading (WCAG 2.4.6) ❌ CRITICAL

### Issue
Content pages (e.g., `/all-links-2025.html`) have an **empty `<h1>` tag**:

```html
<h1 class="post-title"></h1>
```

The page title is set in `<h2>` instead:

```html
<h2 id="show-links-from-the-ride-home-podcast">Show links from The Ride Home Podcast</h2>
```

### Impact
- **Severity:** Critical
- **Users Affected:** Screen reader users, SEO
- **WCAG Level:** AA (fails)
- Screen readers announce empty heading
- Confusing document outline (h2 before h1)
- Poor SEO (search engines rely on h1 for page topic)

### Recommendation
**Option 1:** Add page title to h1:
```html
<h1 class="post-title">Show Links 2025</h1>
```

**Option 2:** Remove empty h1 if Minima theme allows, promote h2 to h1:
```html
<h1 id="show-links-from-the-ride-home-podcast">Show links from The Ride Home Podcast</h1>
```

---

## 3. Missing Skip Navigation Link (WCAG 2.4.1) ⚠️ MODERATE

### Issue
No "skip to main content" link for keyboard users.

### Impact
- **Severity:** Moderate
- **Users Affected:** Keyboard-only users, screen reader users
- **WCAG Level:** AA (recommended, not required for simple sites)
- Keyboard users must tab through header links on every page
- Minor annoyance on simple site, but best practice

### Recommendation
Add skip link before header:

```html
<a href="#main-content" class="skip-link">Skip to main content</a>

<header class="site-header">...</header>
<main id="main-content" class="page-content">...</main>
```

```css
.skip-link {
  position: absolute;
  top: -40px;
  left: 0;
  background: var(--bg-secondary);
  color: var(--text-primary);
  padding: 8px;
  z-index: 100;
}

.skip-link:focus {
  top: 0;
}
```

---

## 4. No Navigation Landmark (WCAG 1.3.1) ⚠️ MODERATE

### Issue
Homepage link lists lack `<nav>` semantic landmark.

### Current Structure
```html
<p><strong>Recent Stuff</strong></p>
<ul>
  <li><a href="/all-links-2025.html">Show Links by Day 2025</a></li>
  ...
</ul>
```

### Impact
- **Severity:** Moderate
- **Users Affected:** Screen reader users
- **WCAG Level:** AA (partially compliant - landmarks help but not required)
- Screen reader users can't jump directly to navigation regions
- Harder to understand page structure

### Recommendation
Wrap navigation lists in `<nav>` elements:

```html
<nav aria-label="Recent content">
  <h2>Recent Stuff</h2>
  <ul>
    <li><a href="/all-links-2025.html">Show Links by Day 2025</a></li>
    ...
  </ul>
</nav>

<nav aria-label="Archive">
  <h2>Older Stuff</h2>
  <ul>...</ul>
</nav>

<nav aria-label="Wrapped reports">
  <h2>Wrapped Archive</h2>
  <ul>...</ul>
</nav>
```

---

## 5. Focus Indicator Visibility (WCAG 2.4.7) ⚠️ MODERATE

### Current Implementation
```css
a:focus,
button:focus {
  outline: 2px solid var(--accent-blue);
  outline-offset: 2px;
}
```

### Issue
Outline color (`--accent-blue: #268bd2`) has **low contrast against light background**:
- Light theme: 3.41:1 (fails 3:1 minimum for UI components)
- Dark theme: 4.08:1 (passes)

### Impact
- **Severity:** Moderate
- **Users Affected:** Keyboard-only users with low vision
- **WCAG Level:** AA (fails for light theme)

### Recommendation
Use higher contrast focus color:

```scss
:root {
  --focus-indicator: #1c6fa0;  // Darker blue, 4.8:1 on light
}

[data-theme="dark"] {
  --focus-indicator: #3ca0e6;  // Lighter blue, 4.9:1 on dark
}

a:focus,
button:focus {
  outline: 2px solid var(--focus-indicator);
  outline-offset: 2px;
}
```

---

## 6. Theme Toggle Button Accessibility ⚠️ MINOR

### Current Implementation
```html
<button class="theme-toggle" id="theme-toggle" aria-label="Toggle dark mode">
  <span class="theme-toggle-icon">☀️</span>
</button>
```

### Issues
1. **Static ARIA label** - doesn't reflect current state
2. **Missing `aria-pressed` or `aria-checked`** - button state not announced
3. **Icon-only button** - relies solely on emoji

### Impact
- **Severity:** Minor
- **Users Affected:** Screen reader users
- **WCAG Level:** AA (partially compliant - label exists but incomplete)
- Screen reader users can't tell current theme state
- Label says "Toggle dark mode" even when in dark mode

### Recommendation
Update JavaScript to manage state:

```javascript
function updateToggleButton(theme) {
  const icon = document.querySelector('.theme-toggle-icon');
  const button = document.getElementById('theme-toggle');

  if (theme === THEME_DARK) {
    icon.textContent = '🌙';
    button.setAttribute('aria-label', 'Switch to light mode');
    button.setAttribute('aria-pressed', 'true');  // ADD
  } else {
    icon.textContent = '☀️';
    button.setAttribute('aria-label', 'Switch to dark mode');
    button.setAttribute('aria-pressed', 'false');  // ADD
  }
}
```

Alternative: Use `role="switch"` with `aria-checked`:

```html
<button class="theme-toggle" role="switch" aria-checked="false" aria-label="Dark mode">
  <span class="theme-toggle-icon">☀️</span>
</button>
```

---

## 7. Responsive Meta Tag ⚠️ MINOR

### Current Implementation
```html
<meta name="viewport" content="width=device-width, initial-scale=1">
```

### Recommendation
Add `user-scalable=yes` explicitly (though not disabling is default):

```html
<meta name="viewport" content="width=device-width, initial-scale=1, user-scalable=yes">
```

This ensures text can be zoomed to 200% (WCAG 1.4.4 requirement). Currently compliant by default.

---

## Accessibility Strengths ✓

### 1. Semantic HTML Landmarks
- ✓ Proper `<header>`, `<main>`, `<footer>` usage
- ✓ Semantic structure aids screen reader navigation

### 2. Language Declaration
- ✓ `<html lang="en">` properly declared
- ✓ Enables correct pronunciation for screen readers

### 3. Descriptive Link Text
- ✓ All 1,498 links use meaningful text (article headlines)
- ✓ No generic "click here" or "read more" links
- ✓ No empty links found

### 4. Keyboard Navigation
- ✓ Theme toggle is native `<button>` element
- ✓ Automatic Enter/Space key support
- ✓ All interactive elements keyboard accessible

### 5. ARIA Usage
- ✓ `aria-label` on theme toggle button
- ✓ `aria-label="Content"` on main landmark
- ✓ `role="banner"` on header

### 6. No Images
- ✓ No images = no alt text issues
- ✓ Emoji used for decoration only (theme toggle icons)

### 7. Responsive Design
- ✓ Mobile-friendly viewport meta tag
- ✓ Text scales properly
- ✓ Touch targets sized appropriately (theme toggle: 0.4em × 0.8em padding)

### 8. Content Structure
- ✓ Consistent date formatting
- ✓ Clear visual hierarchy
- ✓ Logical tab order

---

## Testing Methodology

### Automated Checks
- Color contrast ratios calculated using WCAG formula
- HTML structure validation via regex parsing
- Semantic element detection
- Link text analysis (1,498 links checked)

### Manual Review
- Visual inspection of rendered HTML
- Keyboard navigation flow analysis
- Screen reader consideration (VoiceOver patterns)
- ARIA attribute validation

### Tools Simulated
- WAVE (WebAIM) principles
- axe DevTools criteria
- Lighthouse accessibility audit standards

---

## Priority Recommendations

### High Priority (Fix Immediately)
1. **Fix link contrast** - Darken link colors or increase font size
2. **Fix empty h1** - Add page title to heading
3. **Fix light theme body text contrast** - Darken body text color

### Medium Priority (Fix Soon)
4. **Add skip link** - Improve keyboard navigation
5. **Add nav landmarks** - Wrap navigation lists
6. **Fix focus indicator contrast** - Use higher contrast outline color

### Low Priority (Nice to Have)
7. **Improve theme toggle ARIA** - Add `aria-pressed` state
8. **Add `<article>` tags** - Wrap individual show links in semantic elements

---

## WCAG 2.1 Compliance Summary

| Criterion | Level | Status | Notes |
|-----------|-------|--------|-------|
| 1.3.1 Info and Relationships | A | ⚠️ Partial | Missing nav landmarks |
| 1.4.3 Contrast (Minimum) | AA | ❌ Fail | Links and body text fail |
| 1.4.4 Resize Text | AA | ✓ Pass | Text scales to 200% |
| 1.4.10 Reflow | AA | ✓ Pass | Responsive design works |
| 2.1.1 Keyboard | A | ✓ Pass | All functions keyboard accessible |
| 2.1.2 No Keyboard Trap | A | ✓ Pass | No traps detected |
| 2.4.1 Bypass Blocks | A | ⚠️ Partial | No skip link (recommended) |
| 2.4.2 Page Titled | A | ✓ Pass | All pages have titles |
| 2.4.4 Link Purpose | A | ✓ Pass | Descriptive link text |
| 2.4.6 Headings and Labels | AA | ❌ Fail | Empty h1 tags |
| 2.4.7 Focus Visible | AA | ⚠️ Partial | Low contrast in light theme |
| 3.1.1 Language of Page | A | ✓ Pass | lang="en" declared |
| 3.2.1 On Focus | A | ✓ Pass | No unexpected context changes |
| 3.2.2 On Input | A | ✓ Pass | No forms with input issues |
| 4.1.2 Name, Role, Value | A | ⚠️ Partial | Theme toggle missing state |

**Current Compliance:** **Fails WCAG 2.1 Level AA** due to contrast and heading issues.

**With Fixes:** Would achieve **WCAG 2.1 Level AA compliance**.

---

## Next Steps

1. **Create GitHub issue** for contrast fixes (high priority)
2. **Update Solarized color palette** with accessible variants
3. **Fix empty h1 tags** in Jekyll templates
4. **Add skip link** to header include
5. **Re-test** after fixes with automated tools (WAVE, axe)
6. **Consider user testing** with screen reader users

---

## Appendix: Color Recommendations

### Accessible Solarized Palette (WCAG AA Compliant)

```scss
/* Light Theme - Accessible Variants */
$base00-accessible: #556873;  // Body text (was #657b83)
$base01-accessible: #485e6a;  // Headings (was #586e75)
$blue-accessible:   #1c6fa0;  // Links (was #268bd2)
$violet-accessible: #5858a8;  // Visited (was #6c71c4)

/* Dark Theme - Accessible Variants */
$blue-dark-accessible:   #3ca0e6;  // Links (was #268bd2)
$violet-dark-accessible: #8989d8;  // Visited (was #6c71c4)
```

These maintain the Solarized aesthetic while meeting WCAG AA requirements.
