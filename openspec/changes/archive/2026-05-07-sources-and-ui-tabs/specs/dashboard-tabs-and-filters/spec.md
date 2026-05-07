## ADDED Requirements

### Requirement: Dashboard MUST provide three tabbed views with usable filtering
The dashboard SHALL provide three tabs named `Tổng quan`, `Theo nguồn`, and `Theo vai trò`. Each tab MUST preserve the current page state in-memory without full page reload, and each tab MUST expose filters that remain readable and operable when many filter options exist.

#### Scenario: Switching tabs keeps the user in the dashboard flow
- **WHEN** the user switches between `Tổng quan`, `Theo nguồn`, and `Theo vai trò`
- **THEN** the dashboard SHALL update the active tab view without a full browser page reload

#### Scenario: Source filters remain usable with many sources
- **WHEN** the user opens the `Theo nguồn` tab and there are many source chips
- **THEN** the dashboard SHALL present the chips in a layout that is easy to scan and does not depend on long horizontal scrolling as the primary interaction on desktop

#### Scenario: Role filters remain usable on mobile
- **WHEN** the user opens the `Theo vai trò` tab on a narrow viewport
- **THEN** the dashboard SHALL keep filter controls visible, tappable, and non-overlapping with insight cards

### Requirement: Insight cards MUST emphasize action-oriented comprehension
Insight cards SHALL help a Vietnamese-speaking user quickly understand what changed, why it matters, and who is affected. The card presentation MUST reduce reliance on long English titles as the only entry point to meaning.

#### Scenario: User can identify the main change quickly
- **WHEN** a user scans an insight card
- **THEN** the card SHALL communicate the primary change or signal without requiring the user to parse the original English title alone

#### Scenario: User can understand why the item matters
- **WHEN** a user reads an insight card summary section
- **THEN** the card SHALL communicate why the signal is noteworthy in practical terms, not only restate the source article

#### Scenario: User can identify impacted roles
- **WHEN** an insight has affected roles
- **THEN** the card SHALL display those roles clearly enough for the user to understand who is impacted

### Requirement: Pagination MUST support direct navigation across many pages
The dashboard SHALL retain pagination, and pagination controls MUST support direct access to non-adjacent pages. The control MUST remain operable for large result sets and on small screens.

#### Scenario: User navigates with numbered pages
- **WHEN** there are multiple pages of insight cards
- **THEN** the dashboard SHALL show numbered page controls with the current page highlighted

#### Scenario: User jumps directly to a target page
- **WHEN** the user enters a page number manually
- **THEN** the dashboard SHALL navigate to that page if it is within the valid range

#### Scenario: User sees condensed pagination for long result sets
- **WHEN** the total number of pages is large
- **THEN** the dashboard SHALL use ellipsis or equivalent condensed controls while preserving access to the first, current-nearby, and last pages

### Requirement: Impact badges and time metadata MUST be visually consistent and readable
Impact badges SHALL use consistent sizing and alignment across cards. Time metadata SHALL remain understandable for Vietnamese-speaking users and MUST remain readable on both desktop and mobile.

#### Scenario: Impact badges stay consistent across different labels
- **WHEN** cards display different impact labels such as `Cao`, `Trung bình`, and `Thấp`
- **THEN** the dashboard SHALL render those labels with consistent badge structure and alignment rather than decorative shapes of inconsistent size

#### Scenario: Relative time stays understandable
- **WHEN** a card displays publish time metadata
- **THEN** the dashboard SHALL present a human-readable relative time and SHALL provide a clear absolute-date fallback when relative phrasing is less useful

#### Scenario: Mobile layout keeps metadata readable
- **WHEN** the dashboard is displayed at approximately 375px viewport width
- **THEN** badge and time metadata SHALL remain legible and SHALL not overlap or break card layout

### Requirement: The change MUST include browser verification for responsive and content-quality edge cases
The implementation SHALL be verified in the browser against the responsive layout, arXiv parsing, and Vietnamese content display scenarios that motivated the refinement work.

#### Scenario: Responsive layout verified at 375px
- **WHEN** browser verification is performed at a viewport near 375px width
- **THEN** the dashboard SHALL stack layout sections correctly and keep tabs, filters, cards, and pagination usable

#### Scenario: arXiv insight rendering verified
- **WHEN** browser verification is performed on arXiv-backed insights
- **THEN** titles, extracted article meaning, and associated metadata SHALL appear coherent enough for users to understand the research signal

#### Scenario: VnExpress Vietnamese rendering verified
- **WHEN** browser verification is performed on VnExpress-backed insights
- **THEN** Vietnamese text SHALL render correctly without mojibake or broken encoding in the dashboard
