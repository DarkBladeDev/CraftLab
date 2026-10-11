# Spec Delta: block-studio

## ADDED Requirements

### Requirement: Prop State Sound and Particle Triggers
The Block Studio prop state editor SHALL provide interface selectors allowing authors to bind registered sound events (from the workspace sound events registry) and particle definitions (from the workspace particle registry) to individual prop state definitions, specifying particle spawn offsets and volume/pitch attributes for state entry events.

#### Scenario: Binding sound and particle triggers to a prop state
- **WHEN** author configures an entry sound effect and particle trigger on a prop's `open` state
- **THEN** system saves the audio and particle references into the block definition state machine and displays active media linkage badges in the state inspector
