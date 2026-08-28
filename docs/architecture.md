# Architecture Notes

The intended design separates data acquisition from analysis:

1. **Acquisition** — obtain data through approved interfaces or documented imports.
2. **Validation** — check required fields, types, timestamps, and source identity.
3. **Normalisation** — map source-specific records into a common internal schema.
4. **Storage** — keep raw and processed data separate, with provenance metadata.
5. **Analysis** — calculate descriptive comparisons and theoretical scenarios.
6. **Presentation** — show assumptions, timestamps, and limitations alongside results.

The first implementation should focus on the common schema and validation layer before adding live integrations.
