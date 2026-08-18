# Borealis Forum Toronto retrieval route

**Checked:** 2026-08-17  
**Scope:** the three Toronto municipal Forum Research datasets for which access was requested: 2013, 2014, and 2018  
**Method:** public Borealis metadata API, the University of Toronto Map and Data Library catalogue, and the official Dataverse Data Access API documentation. No credentials were used and no restricted file was downloaded.

## Result

The three requests cover **37 respondent datasets**, each paired with a public Word codebook:

| Collection | DOI | Public documentation | Restricted respondent data | Notes |
|---|---|---:|---:|---|
| Toronto municipal 2013 | [10.5683/SP3/2ANYFR](https://doi.org/10.5683/SP3/2ANYFR) | 12 `.docx` codebooks | 12 ingested `.tab` files, with original `.sav` files retained | All 12 codebooks are labelled `incomplete`; categories run from January to December, with two April studies and no March category. |
| Toronto municipal 2014 | [10.5683/SP3/IM2A0R](https://doi.org/10.5683/SP3/IM2A0R) | 15 `.docx` codebooks | 15 ingested `.tab` files, with original `.sav` files retained | Borealis describes this as 15 datasets from 2014. |
| Toronto municipal 2018 | [10.5683/SP2/QCPM89](https://doi.org/10.5683/SP2/QCPM89) | 10 `.docx` codebooks | 10 ingested `.tab` files, with original `.sav` files retained | The pairs are February, June, July 26–29, July 27, August, September 6, September 20–23, October 1–3, October 9–10, and October 19. |
| **Total** | — | **37 public files** | **37 restricted files** | **74 files in the published metadata.** |

The counts, restriction flags, file identifiers, checksums, ingested formats, and original filenames are exposed by Borealis's public metadata API:

- [2013 metadata API](https://borealisdata.ca/api/datasets/:persistentId/?persistentId=doi:10.5683/SP3/2ANYFR)
- [2014 metadata API](https://borealisdata.ca/api/datasets/:persistentId/?persistentId=doi:10.5683/SP3/IM2A0R)
- [2018 metadata API](https://borealisdata.ca/api/datasets/:persistentId/?persistentId=doi:10.5683/SP2/QCPM89)

The University of Toronto [Forum Research collection page](https://mdl.library.utoronto.ca/collections/numeric-data/microdata/forum-research-political-polls) independently describes the collection as monthly Forum federal, provincial, and Toronto municipal opinion polls from 2013 onward, restricted for download to Ontario-university students, staff, and faculty; other researchers may request access.

These 37 surveys are **not automatically 37 usable mayoral polls**. The archive is broader than the repository's election-poll inventory. In particular, the 2018 collection has ten surveys while the legacy corpus has five Forum 2018 mayoral proxies. The codebooks and ballot variables must determine which studies contain a relevant mayoral question, which candidate scenario was asked, and whether several readings came from one respondent sample.

## What is available before approval

All 37 codebooks are marked unrestricted in the current Borealis metadata. They can be downloaded through the browser or the unauthenticated file endpoint `/api/access/datafile/{file-id}`. Screening those codebooks now can identify likely mayoral surveys and variable names, although the 2013 codebooks' explicit `incomplete` label means the respondent files may still be necessary to recover value labels and weights.

Public metadata also establishes that the restricted files were uploaded as SPSS `.sav` files and ingested by Dataverse as tab-delimited `.tab` files. The default access endpoint returns the archival tabular representation; adding `format=original` requests the saved SPSS original. Retaining both representations is useful: `.tab` is simple to audit, while `.sav` may preserve labels and measurement metadata more faithfully.

## Minimal workflow after access is granted

The simplest route requires no API token:

1. Sign in to the same Borealis account used for the requests and open each DOI.
2. Confirm that the restricted data rows now offer download rather than `Request Access`.
3. Download the complete dataset once in archival/tabular format and once in original/SPSS format, if the interface offers both choices.
4. Put the six resulting bundles under `data/source_documents/restricted_forum_borealis/`, which is already covered by the repository's `data/source_documents/` ignore rule, and give Codex only the local paths—not account credentials or an API token.
5. Verify that the bundles contain 12, 15, and 10 data files respectively. Preserve each bundle, `MANIFEST.TXT`, retrieval timestamp, DOI/version, and checksum before extraction.

For reproducible bulk retrieval, Borealis is running Dataverse 6.8.4-SP and supports the standard Data Access API. The official [Dataverse Data Access API guide](https://guides.dataverse.org/en/latest/api/dataaccess.html) documents whole-dataset ZIP downloads, authenticated with the `X-Dataverse-key` header. It also states that the bundle contains every file the account can access and a `MANIFEST.TXT`; restricted files are omitted if the account has not been granted access. The same guide documents `format=original` for retrieving the saved source format rather than the ingested `.tab` form.

An API token is optional. If used, create it in Borealis's **API Token** account tab and treat it as a password. The official [Dataverse authentication guide](https://guides.dataverse.org/en/latest/api/auth.html) recommends the HTTP header rather than placing the token in a URL. A local-only retrieval pattern is:

```bash
read -r -s BOREALIS_TOKEN

curl --fail-with-body --location \
  --header "X-Dataverse-key: ${BOREALIS_TOKEN}" \
  --output forum-toronto-2013-tab.zip \
  'https://borealisdata.ca/api/access/dataset/:persistentId/?persistentId=doi:10.5683/SP3/2ANYFR'

curl --fail-with-body --location \
  --header "X-Dataverse-key: ${BOREALIS_TOKEN}" \
  --output forum-toronto-2013-sav.zip \
  'https://borealisdata.ca/api/access/dataset/:persistentId/?persistentId=doi:10.5683/SP3/2ANYFR&format=original'

unset BOREALIS_TOKEN
```

Repeat the two calls for `doi:10.5683/SP3/IM2A0R` and `doi:10.5683/SP2/QCPM89`. None of the three current dataset versions declares a `guestbookId`, so the published metadata gives no indication that an additional guestbook POST is needed after access approval. The token should never be pasted into chat, committed, or passed as a URL query parameter.

## Rights and publication constraints

The 2013 and 2014 metadata is explicit:

- access is restricted to current Ontario-university faculty, staff, and students;
- redistribution/redissemination is prohibited without written permission; and
- results of analysis may be published with appropriate acknowledgement and source citation.

Those conditions mean the raw `.tab`, `.sav`, and derived respondent-level extracts must remain outside git and should not be sent to collaborators. Aggregate model estimates are much closer to the expressly permitted “results of analysis,” but source acknowledgement and DOI citation remain required.

The 2018 record differs: it displays a CC0 1.0 licence and a restricted-access statement, but no record-level redistribution prohibition or citation requirement. Do not silently import the 2013/2014 terms into 2018, and do not assume that restricted institutional access is irrelevant to downstream sharing. If raw-file redistribution is ever contemplated, ask the Map and Data Library to confirm how the collection-level restriction interacts with the 2018 CC0 record. Internal modelling does not require resolving that edge case.

## Proportionate next step

Do not build a general-purpose microdata platform. Download and text-screen the 37 public codebooks now. When approval arrives, acquire the six small bundles, hash and inventory them, then extract only the variables needed to reproduce a mayoral ballot reading: fieldwork identity/date if present, ballot scenario, response labels, weight, and any decided/leaning filter. Reconcile each reconstructed aggregate to a public Forum release where one exists. Surveys with no mayoral ballot question remain out of the model rather than being forced into the legacy proxy manifest.
