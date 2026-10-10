# Spec Delta: block-studio

## ADDED Requirements

### Requirement: Prop State Machine Authoring
The system SHALL provide interface controls within Block Studio allowing authors to configure multiple named states for a prop definition (such as `off`, `on`, `open`, `closed`), designate a `default_state`, and for each state configure a distinct `block_model`, an optional `light_level` (integer from 0 to 15), an entry `sound` effect with volume and pitch settings, an optional collision override (`solid` or `passable`), and a transition target `next_state`.

#### Scenario: Authoring a two-state toggle prop
- **WHEN** a user defines a prop with `default_state: "off"`, an `"off"` state pointing to `studio:props/lamp_off` with `light_level: 0`, and an `"on"` state pointing to `studio:props/lamp_on` with `light_level: 14` and entry sound `block.wooden_button.click_on`
- **THEN** the system validates both states, links their transition targets cyclically, and saves the configuration to the draft workspace

#### Scenario: Authoring a cyclic multi-state prop
- **WHEN** a user creates a prop with three sequential states (`off` -> `low` -> `high` -> `off`)
- **THEN** the system records the custom state sequence and validates that all `next_state` references point to existing state keys

#### Scenario: Validating light level boundaries
- **WHEN** a user enters a light level outside the integer range 0 to 15 (e.g. -1 or 16)
- **THEN** the system rejects the input and displays a validation error constraining light levels between 0 and 15
