# InSoLiTo Frontend Changes Roadmap

## Frontend Enhancements

### 1. UI Library Integration

- Integrate a UI library, such as Bootstrap.
- Ensure compatibility with current JavaScript libraries, like jQuery.

### 2. Main Page Redesign

- **Objective**: Give users a clear overview of the application's purpose and functionality, with guidance on initial usage.
- Redesign visuals (add images, usage explanations).
- Create a "First Steps" guide to introduce the application's main features.

### 3. UI Modifications

- Explore alternatives to the current lateral menu.
- Refactor lateral menu to integrate with Bootstrap.
- Clarify distinctions between titles and subtitles across the UI.

### 4. API Error Handling

- Implement error-catching for API failures.
- Display an informative error message to users when API issues arise.

### 5. CSS Refinements

- Remove commented-out, unused code (after verification).
- Minimize the use of absolute positioning.
- Check compatibility with Bootstrap CSS to avoid conflicts.

### 6. JavaScript Improvements

- Remove any unused commented code (after verification).
- Standardize DOM manipulation:
  - If using jQuery, ensure all DOM selections and actions utilize jQuery functions.
    - **Example**:

         ```javascript
         // From:
         var YearCanvas = document.getElementById('YearCanvas');

         // To:
         var YearCanvas = $('#YearCanvas');
         ```

- **Menu Search Enhancements**:
  - Add a loading state (e.g., "Searching data…").
  - Display a "No results found" message when no matches are returned.
  - Adjust the size and color of the search icon to fit a gray-scale theme.

- Add comments to key functions to improve future code readability.
- Convert code to ES6 standards for better readability and maintainability (Refer to [Learn ES6](https://babeljs.io/docs/learn/)).
- Move inline JavaScript styling (colors, etc.) to CSS classes for consistency.