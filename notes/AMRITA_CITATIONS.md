# Amrita-affiliated citation candidates

Date: 2026-10-11. Nothing here has been added to paper/refs.bib.

## Method and honesty notes

- Discovery: OpenAlex works filtered to institution "Amrita Vishwa Vidyapeetham" (I81556334) plus topic keywords. OpenAlex institution tags are noisy (many false positives), so every accepted paper was re-checked against the raw affiliation strings deposited with the paper (OpenAlex raw_affiliation_strings / Crossref author affiliation / amrita.edu publication page).
- Abstracts: read via OpenAlex (inverted index) or an amrita.edu publication page. IEEE Xplore, ScienceDirect, Springer and Inderscience block automated fetch, so two papers (A1, A2) have an UNREAD abstract; they are flagged.
- Bibliographic data came from OpenAlex + Crossref. Volume/page fields flagged "check" should be confirmed on the publisher page by the verifier or the human before submission.
- Reality check: no Amrita-affiliated paper was found on intuitive physics, world models, V-JEPA, JEPA, or violation-of-expectation. All fits below are indirect (video anomaly detection, degradation robustness, evaluation artefacts). Each sentence below is written so it is true of the cited paper and does not borrow its authority for our own claims.
- Trap avoided: the well-known video anomaly detection papers by S. Chandrakala and K. Deepak (AI Review 2022, 10.1007/s10462-022-10258-6; ESWA 2021, 10.1016/j.eswa.2021.116168) carry a SASTRA Deemed University affiliation on the paper, even though Dr. K. Deepak now has an Amrita Chennai faculty page. Rejected as "Amrita-affiliated paper".

## Summary table

| # | Paper | Venue / year | Amrita (confirmed where) | Abstract read | Fit | Verdict |
|---|---|---|---|---|---|---|
| 1 | Veetil et al., data leakage and generalizability, MRI Parkinson's CNNs | Digital Signal Processing 147 (2024) | Amrita School of AI, Coimbatore/Bengaluru (OpenAlex raw affil + amrita.edu page) | Yes (amrita.edu) | Evaluation artefacts inflate accuracy; maps onto our splice finding | ACCEPT |
| 2 | Koushik et al., smartphone handwritten doc images, robust to blur/low light | IEEE Access 13 (2025) | Amrita School of Computing, Mysuru | Yes | Graded-severity blur / low-illumination degradations | ACCEPT (weak-moderate) |
| 3 | Kandacharam, Rajathilagam, Vasudevan, dual EDE unsupervised accident detection | JoVE, issue 223 (2025) | Amrita School of Computing, Coimbatore (first two authors) | Yes | Reconstruction-error score for unsupervised video anomaly detection | ACCEPT (weak-moderate) |
| 4 | Amrutha, Jyotsna, Amudha, suspicious activity detection from surveillance video | IEEE ICIMIA 2020, pp. 335-339 | Amrita School of Engineering, Bengaluru | Yes | Video surveillance, normal vs suspicious activity | ACCEPT (weak) |
| 5 | Anjali S, Don S, explainable VAD with Video Masked Autoencoders + ConvLSTM | IEEE Open J. Comput. Soc. (2026), pp. 1-12 | Amrita School of Computing, Amritapuri (Crossref author affil) | NO (publisher blocked); title only | Masked video autoencoder used for anomaly scoring, closest topic to V-JEPA | BORDERLINE, accept after the verifier reads the abstract |
| 6 | Jayaprasad, Menon, Anjali T, EfficientNet recognition of sign language alphabets (LSE) | IEEE ICECMSN 2025, pp. 220-225 | Amrita, Dept. of CSE (Crossref + OpenAlex) | Yes | Author's own paper; EfficientNetB0 + XAI | BORDERLINE self-citation, weak fit |
| 7 | Randieri et al. (Ganesh, Raj from Amrita), UAV detection under adverse conditions | Drones 9(8):549 (2025) | Amrita School of AI, Coimbatore (2 of 6 authors) | Yes | Vision systems degrade under motion blur, low light | BORDERLINE (generic review) |
| 8 | Anjali S, Don S, Generalised video anomaly detection: a systematic review | Int. J. Comput. Vis. Robotics 15(4):431-458 (2025) | Same authors as #5; affiliation not verified from deposited metadata for this paper | NO | Survey of VAD | BORDERLINE, unverified; affiliation needs check |

Strong fits: 1 only. Moderate/weak but honest: 2, 3, 4, 5. That makes 5 usable plus 3 borderline. Fewer than 6 strong fits exist; see "If you need six" at the bottom.

---

## Accepted / borderline entries with sentence, placement, bibtex

### 1. veetil2024 (ACCEPT)
Evidence (amrita.edu publication page, abstract summary): 12 pretrained CNNs on T1-weighted MRI from PPMI, top three tested on external cohorts under simulated subject-wise, slice-wise and longitudinal leakage; "slice level data leakage and longitudinal data leakage can result in over 67% and 30% inflation of accuracy score"; Grad-CAM used for explanation.
Where: 05_discussion.tex, paragraph "What this implies for how VoE results are reported" (and optionally the sentence in "How these fit together" that frames the splice structure as a property of the benchmark).
Sentence: "A high accuracy can reflect an unintended property of the evaluation data rather than what the model has learned; for example, slice-level data leakage inflated MRI classification accuracy by more than 67\% in one study \cite{veetil2024}."
Caveat: medical imaging, different mechanism (train/test leakage, not within-video splice). Cite only as an example that benchmark structure can inflate accuracy. Do not say it is the same phenomenon.
```
@article{veetil2024,
  author  = {Veetil, Iswarya Kannoth and Chowdary, Divi Eswar and Chowdary, Paleti Nikhil and Sowmya, V. and Gopalakrishnan, E. A.},
  title   = {An analysis of data leakage and generalizability in {MRI} based classification of {Parkinson's} Disease using explainable {2D} convolutional neural networks},
  journal = {Digital Signal Processing},
  volume  = {147},
  pages   = {104407},
  year    = {2024},
  doi     = {10.1016/j.dsp.2024.104407}
}
```

### 2. koushik2025 (ACCEPT, weak-moderate)
Evidence (abstract read): classification of smartphone-captured document images degraded by blur, low illumination and shadows, with two to three synthetic severity levels each, compared against nine deep classifiers; reports robustness across severity levels.
Where: 03_method.tex or 02_related_work.tex, where blur / brightness edits with graded strengths are introduced. Only for the statement that graded degradation levels are a standard way to probe deep image models.
Sentence: "Graded severity levels of blur and illumination change have been used to study deep image models under degradation \cite{koushik2025}."
Caveat: image (document) classification, not video, and not a non-robustness result. Check volume/pages on Xplore (online Dec 2024, vol 13 is 2025).
```
@article{koushik2025,
  author  = {Koushik, K. S. and Nair, B. J. Bipin and Rani, N. Shobha and Javed, Mohammed},
  title   = {Robust Classification of Smartphone Captured Handwritten Document Images Using Deep Learning},
  journal = {IEEE Access},
  volume  = {13},
  pages   = {14922--14948},
  year    = {2025},
  doi     = {10.1109/ACCESS.2024.3520327}
}
```

### 3. kandacharam2025 (ACCEPT, weak-moderate)
Evidence (abstract read): two shared encoder-decoder pipelines; phase 1 learns to reconstruct normal driving with a reconstruction loss "to characterize normal behavior"; used for unsupervised accident / anomaly detection in surveillance video.
Where: 02_related_work.tex, new sentence in "Impossible versus improbable" or a short "Anomaly detection" sentence: error-based scores in video anomaly detection flag deviation from learned normal.
Sentence: "Unsupervised video anomaly detectors likewise score events by how poorly a model trained on normal footage reconstructs them \cite{kandacharam2025}, which flags what is unusual rather than what is physically impossible."
(The clause after the comma is our framing, not the paper's claim; keep it outside the citation's scope or rephrase as "which raises the same question for those scores".)
Caveat: JoVE is a methods journal; traffic footage. Check the JoVE article id (e68731 style) before submission.
```
@article{kandacharam2025,
  author  = {Kandacharam, Sneha and Rajathilagam, B. and Vasudevan, Shriram K.},
  title   = {Dual Encoder-Decoder-Encoder with Adversarial Training for Unsupervised Traffic Accident Detection in Surveillance Videos},
  journal = {Journal of Visualized Experiments},
  number  = {223},
  year    = {2025},
  doi     = {10.3791/68731}
}
```

### 4. amrutha2020 (ACCEPT, weak)
Evidence (abstract read): deep-learning classifier of suspicious vs normal activity from features of consecutive frames in an academic environment, with alerts.
Where: 02_related_work.tex, same anomaly-detection sentence as #3 (cite both together).
Sentence: "Deep video models are used to flag unusual or suspicious behaviour in surveillance footage \cite{amrutha2020}."
Caveat: supervised two-class classifier, low depth. Cite only for the plain fact that video models are applied to unusual-event detection.
```
@inproceedings{amrutha2020,
  author    = {Amrutha, C. V. and Jyotsna, C. and Amudha, J.},
  title     = {Deep Learning Approach for Suspicious Activity Detection from Surveillance Video},
  booktitle = {Proc. 2nd Int. Conf. Innovative Mechanisms for Industry Applications (ICIMIA)},
  pages     = {335--339},
  year      = {2020},
  doi       = {10.1109/ICIMIA48430.2020.9074920}
}
```
(Proceedings title as listed by OpenAlex: International Conference on Innovative Mechanisms for Industry Applications; the "2nd" and edition wording should be checked on Xplore.)

### 5. anjali2026 (BORDERLINE: abstract unread)
Evidence: Crossref lists both authors at "Amrita School of Computing, Amrita Vishwavdyapeetham" (sic), Amritapuri. Title states video masked autoencoders + ConvLSTM for explainable video anomaly detection. Abstract, volume and article number could not be retrieved (Xplore blocked; DOI redirects to https://ieeexplore.ieee.org/document/11707675).
Where: 02_related_work.tex, "Latent prediction and intuitive physics" paragraph, next to the VideoMAE V2 sentence, or the anomaly-detection sentence.
Sentence (only after the abstract is read; keep minimal): "Masked video autoencoders have also been used for video anomaly detection \cite{anjali2026}."
Action needed: human or verifier opens https://doi.org/10.1109/OJCS.2026.3737277 in a browser, confirms the abstract mentions a video masked autoencoder and anomaly scoring, and fills volume/pages.
```
@article{anjali2026,
  author  = {Anjali, S. and Don, S.},
  title   = {Explainable Video Anomaly Detection Using Video Masked Autoencoders and Convolutional {LSTM}},
  journal = {IEEE Open Journal of the Computer Society},
  pages   = {1--12},
  year    = {2026},
  doi     = {10.1109/OJCS.2026.3737277}
}
```
(Author initials: Crossref gives given name "Anjali", family "S" and given "Don", family "S", i.e. the initial is the family-name slot; confirm full names on the paper page.)

### 6. jayaprasad2025 (BORDERLINE self-citation)
Evidence (abstract read): LSE (Spanish sign language) alphabet recognition, CNN based on EfficientNetB0 with explainable AI; ~2,500 images, 19 static letters; 95.73% test accuracy. Authors Vidyasree Jayaprasad, Anand Rodriguez Menon, Tricha Anjali; all "Amrita Vishwa Vidyapeetham, Department of Computer Science and Engineering". Conference held in Coimbatore, 24-26 Nov 2025, IEEE.
Where: 05_discussion.tex "Scope" or "Limitations", or the acknowledgements sentence on prior work. A truthful, low-key use: "Explanation maps such as Grad-CAM are a common way to inspect what a trained image classifier uses \cite{jayaprasad2025}; our frozen-model probe instead edits the input and observes the verdict."
Caveat: the paper is about a trained static-image classifier, unrelated to video or physics. It is mainly a disclosure/self-citation. Do not cite if the reviewers could read it as padding; the human decides. Also confirm that the paper does use Grad-CAM specifically (abstract only says "explainable AI").
```
@inproceedings{jayaprasad2025,
  author    = {Jayaprasad, Vidyasree and Menon, Anand Rodriguez and Anjali, Tricha},
  title     = {Towards Inclusive {AI}: {EfficientNet}-based Recognition of Sign Language Alphabets},
  booktitle = {Proc. 5th Int. Conf. Evolutionary Computing and Mobile Sustainable Networks (ICECMSN)},
  pages     = {220--225},
  year      = {2025},
  publisher = {IEEE},
  doi       = {10.1109/ICECMSN68058.2025.11382596}
}
```

### 7. randieri2025 (BORDERLINE)
Evidence (abstract read): review of obstacle and aircraft detection for UAVs in fog, rain, smoke, low light, motion blur; discusses "performance strengths and limitations under degraded sensing conditions". Amrita School of Artificial Intelligence, Coimbatore: Sudarshan Ganesh, Rayappa David Amar Raj.
Where: 01_introduction.tex or 03_method.tex motivation for the invariance test: degraded sensing (blur, low light) is a known difficulty for learned vision.
Sentence: "Degraded imaging conditions such as motion blur and low light are a recognised difficulty for learned vision systems \cite{randieri2025}."
Caveat: generic review (MDPI Drones), not about video prediction.
```
@article{randieri2025,
  author  = {Randieri, Cristian and Ganesh, Sudarshan and Raj, Rayappa David Amar and Yanamala, Rama Muni Reddy and Pallakonda, Archana and Napoli, Christian},
  title   = {Aerial Autonomy Under Adversity: Advances in Obstacle and Aircraft Detection Techniques for Unmanned Aerial Vehicles},
  journal = {Drones},
  volume  = {9},
  number  = {8},
  pages   = {549},
  year    = {2025},
  doi     = {10.3390/drones9080549}
}
```

### 8. anjali2025 (BORDERLINE, unverified)
Systematic review of generalised video anomaly detection, Int. J. Computational Vision and Robotics 15(4):431-458, 2025, doi 10.1504/IJCVR.2025.147490. Crossref gives authors "S. Anjali" and "S. Don" with no affiliation; they appear to be the same authors as #5, but Amrita affiliation is NOT confirmed from this paper's metadata and the abstract was not readable (Inderscience 403). Do not cite unless the human confirms both on the Inderscience page.
Possible placement: same anomaly-detection sentence as #3-#5: "Surveys of video anomaly detection \cite{anjali2025}."
```
@article{anjali2025,
  author  = {Anjali, S. and Don, S.},
  title   = {Generalised video anomaly detection: a systematic review},
  journal = {International Journal of Computational Vision and Robotics},
  volume  = {15},
  number  = {4},
  pages   = {431--458},
  year    = {2025},
  doi     = {10.1504/IJCVR.2025.147490}
}
```

---

## Full log of candidates considered

Accepted / borderline: see above (#1-#8).

Rejected (reason):
- Chandrakala, Deepak, Revathy, AI Review 2022 (10.1007/s10462-022-10258-6): VAD review, but paper affiliation is SASTRA, not Amrita.
- Chandrakala, Deepak, Vignesh, ESWA 2021 (10.1016/j.eswa.2021.116168): same, SASTRA affiliation.
- Natarajan et al., wild animal activity detection, IEEE Access 2023 (10.1109/ACCESS.2023.3289586): Amrita Chennai confirmed, abstract read; VGG19+Bi-LSTM animal detection with SMS alerts, no relevance.
- Aloysius, Geetha, Nedungadi, Efficient ConSignformer, IEEE OJCS 2025 (10.1109/OJCS.2025.3564828); Aloysius et al., IEEE Access 2021 (10.1109/ACCESS.2021.3122921); Geetha et al., IEEE Access 2025 (10.1109/ACCESS.2025.3554618): Amrita confirmed; video / sign language transformers. No honest sentence in our paper needs them; rejected as padding.
- Sikha and Soman, DMD salient region detection in noisy images (SIViP, 10.1007/s11760-019-01539-9): Amrita CEN confirmed; abstract not retrievable; image saliency, not relevant.
- Guna, Sikha, Benitez, Interpreting CNN predictions with cGANs (Knowledge-Based Systems 302, 2024, 10.1016/j.knosys.2024.112340): Amrita Coimbatore confirmed; abstract read (Grad-CAM-driven explanation generator). Not relevant to a frozen-surprise probe.
- Jacob, Sowmya et al., wound grading with perturbation-based XAI (CMPB 2025, 10.1016/j.cmpb.2025.108981): Amrita confirmed; medical wounds, not relevant.
- Kandacharam et al., Fusion Framework for Accident Anticipation in Dashcam Videos (SN Comput Sci 6(5):548, 2025, 10.1007/s42979-025-04085-z): Amrita confirmed; abstract unreadable (Springer blocked); accident anticipation is related to prediction, but cannot be cited without reading it. Unverified.
- Rajan and Parameswaran, key frame extraction for surveillance videos (Sci Rep 15, 2025, 10.1038/s41598-024-84324-0): Amrita confirmed; abstract read; key frame selection for summarisation, no honest link to our frame-difference baseline without reading methods. Rejected.
- Namitha et al., Advances in DL for Autonomous Vehicle Perception review (JCCE 2025, 10.47852/bonviewjcce52025836): Amrita Amritapuri confirmed; abstract read; 3D detection and sensor fusion, no link.
- Amrita pedestrian intention prediction (Megalingam et al., IJTST 2026, 10.1016/j.ijtst.2025.10.015): not read beyond title; not relevant to physics-violation surprise.
- Sanjeevi et al. echocardiography / fluoroscopy video analysis papers: medical video, no link.
- Gautam and Thangavel, video analytics for smart buildings (Soft Computing 2019): not read; no link.
- Many other OpenAlex hits (image forgery / watermarking / steganography, Sahu et al.; Pallakonda et al. forgery detection) were scanned. Image-tampering detection (e.g. Aryan et al., IEEE Access 2025, 10.1109/ACCESS.2025.3607206, Amrita School of AI confirmed, ViT on CASIA/DEFACTO splicing) is only loosely related to our splice finding (images, document forgery) and is not cited.
- Searches for Amrita papers on: JPEG/compression robustness of deep models, adversarial robustness of vision models, video action recognition benchmarks, self-supervised video representation, world models / intuitive physics / object permanence, surprise or novelty in video prediction found nothing usable (adversarial hits were network-security papers).

## If you need six

With the honest criterion above, there are 4 usable (#1-#4), 1 pending an abstract check (#5), and 3 borderline (#6-#8). Smallest set that gets to six without padding: #1, #2, #3, #4, #5 (after abstract check) and #7 or #6. #1 is the only one that supports a substantive argument in the paper; the rest are supporting citations for background sentences. Recommend the human decides whether citing these is worth the page space, since none of them is on physics or world models.

---

## Verification and critic review

Date: 2026-10-11. Sources used: Crossref `/works/<doi>`, OpenAlex `works/doi:<doi>` (authorships, raw affiliation strings, abstract_inverted_index), Semantic Scholar Graph API. IEEE Xplore, ScienceDirect, doi.org landing pages were not fetchable (anti-bot page), so anything that needed them is marked UNVERIFIED. paper/ was not edited.

### Task A: metadata verification

| # | Title | Authors (order) | Venue / year / vol / pages | DOI resolves in Crossref | Amrita author in record | Result |
|---|---|---|---|---|---|---|
| 1 | exact match | Veetil, Chowdary D.E., Chowdary P.N., Sowmya, Gopalakrishnan: match | Digital Signal Processing 147, art. 104407, Apr 2024: match | yes | OpenAlex raw affil, all 5: Amrita School of AI, Coimbatore/Bengaluru (Crossref has no affil) | VERIFIED. Abstract not obtainable via API (Crossref/OpenAlex/S2 all empty); the "67% / 30%" inflation figures are UNVERIFIED by me (from the earlier agent's amrita.edu read). |
| 2 | exact match | Koushik, Nair, Rani, Javed: match | IEEE Access 13, pp. 14922-14948, 2025 (online Dec 2024): match | yes | Crossref + OpenAlex: Koushik and Nair at Amrita School of Computing, Mysuru | VERIFIED. Abstract read via OpenAlex: blur / low illumination at three severity levels, shadow at two, compared with nine models. |
| 3 | exact match | Kandacharam, Rajathilagam, Vasudevan: match | JoVE issue 223, 5 Sep 2025; no volume or page in Crossref | yes | OpenAlex raw affil: Kandacharam, Rajathilagam at Amrita School of Computing, Coimbatore. Vasudevan is Intel, not Amrita | VERIFIED (article id e68731 not in the record: UNVERIFIED, omit). Abstract read via OpenAlex. |
| 4 | exact match | Amrutha, Jyotsna, Amudha: match | 2020 2nd Int. Conf. Innovative Mechanisms for Industry Applications (ICIMIA), Mar 2020, pp. 335-339 | yes | OpenAlex raw affil, all 3: Amrita School of Engineering, Bengaluru | VERIFIED; booktitle corrected (official form includes "2020 2nd"). Abstract read via OpenAlex. |
| 5 | exact match | "Anjali S", "Don S" (Crossref given/family = Anjali / S and Don / S) | IEEE Open J. Comput. Soc., 2026, pp. 1-12 (early access; no volume or issue), OA CC BY | yes (Crossref, S2 both resolve) | Crossref + OpenAlex: Amrita School of Computing, "Amrita Vishwavdyapeetham" (sic) | Metadata VERIFIED. ABSTRACT UNVERIFIED: Crossref, OpenAlex, Semantic Scholar all have no abstract; Xplore and the OA PDF are behind an anti-bot challenge; arXiv has no copy. Only the title is confirmed. Full given names UNVERIFIED. |
| 6 | exact match | Jayaprasad, Menon (Anand Rodriguez), Anjali T: match to Crossref; S2 shows "Anand Menon", "A. T" | 2025 5th Int. Conf. Evolutionary Computing and Mobile Sustainable Networks (ICECMSN), 24 Nov 2025, pp. 220-225 | yes | Crossref, all 3: Amrita Vishwa Vidyapeetham, Dept. of CSE | VERIFIED. Abstract read via S2 (EfficientNetB0 CNN "paired with explainable AI (XAI)", ~2,500 images, 19 static letters, 95.73% test accuracy). Abstract does not name Grad-CAM. Third author's full name ("Tricha") UNVERIFIED (record only says "Anjali T"). |
| 7 | exact match | Randieri, Ganesh, Raj, Yanamala, Pallakonda, Napoli: order OK but BIBTEX GIVEN NAME WAS WRONG | Drones 9(8), 549, 4 Aug 2025: match | yes | Crossref: Ganesh and Raj at Amrita School of AI, Coimbatore | VERIFIED after fix: second author is "Sai Venkata Ganesh", not "Sudarshan Ganesh". Abstract (Crossref) confirms fog, rain, smoke, low light, motion blur. |

Corrections: #7 author name; #4 booktitle; #3 drop article-id talk; #5 and #6 author-name caveats. #8 was not in scope and remains unverified.

### Task B: critic review (hostile)

The paper's claims: V-JEPA surprise is not a reliable physics detector; the possible/impossible verdict flips under harmless edits; splice structure in the benchmark is a confound; frame-difference baselines match. None of the seven papers is about physics, world models or VoE. The honest framing is: these are background citations for generic points. The sentences must therefore make narrow descriptive claims about what each paper did, and never attach authority to our results.

| # | Verdict | Final sentence | Placement | Key |
|---|---|---|---|---|
| 1 | ACCEPT-WITH-REWRITE (relevant by analogy; the only one with a real argumentative role) | "Accuracy can also be inflated by how an evaluation set is built rather than by what the model has learned; slice-level data leakage in an MRI study is one documented example \cite{veetil2024}." Number removed because the 67% figure could not be independently confirmed. Do not equate leakage with our splice structure. | 05_discussion.tex, paragraph "What this implies for how VoE results are reported", after the sentence on accuracy not separating tracking of impossibility from tracking of a correlate | veetil2024 |
| 2 | ACCEPT-WITH-REWRITE (tangential: document images, not video; the paper proposes a classifier and does not study failure) | "Blur and low illumination applied at several graded severity levels are a common way to test image classifiers under degradation \cite{koushik2025}." | 03_method.tex or 02_related_work.tex where blur/brightness strengths are introduced; a trailing clause is enough | koushik2025 |
| 3 | ACCEPT-WITH-REWRITE (tangential; original wording over-claimed that scores are "reconstruction error" and added our own conclusion) | "Video anomaly detection systems of this kind learn a model of normal footage, for example normal driving, and flag deviations from it \cite{kandacharam2025}; whether such a signal separates a physical violation from any other unusual event is the question we ask of V-JEPA surprise." The second clause is our question, not the paper's. | 02_related_work.tex, "Impossible versus improbable" paragraph | kandacharam2025 |
| 4 | ACCEPT-WITH-REWRITE (weak; tangential; supervised classifier, low depth) | "Deep learning classifiers on frame-level features have been applied to separate suspicious from normal activity in surveillance video \cite{amrutha2020}." Cite together with #3 in one sentence, not separately. | 02_related_work.tex, same anomaly-detection sentence as #3 | amrutha2020 |
| 5 | ACCEPT-WITH-REWRITE, CONDITIONAL on a human opening the DOI page and confirming the abstract mentions video masked autoencoders for anomaly detection. Title alone supports the sentence; nothing else about the paper is claimed. | "Video masked autoencoders have also been used as the backbone of video anomaly detection systems \cite{anjali2026}." No claim about explainability, performance or comparison. Closest topic to V-JEPA, but still not about physics. | 02_related_work.tex, "Latent prediction and intuitive physics" paragraph, after the VideoMAE sentence | anjali2026 |
| 6 | ACCEPT-WITH-REWRITE as a self-citation. Fit is weak (static images, trained classifier). It is honest only as a statement about prior work; the human decides whether it is worth the space. | "One of the authors previously used explainability tooling in a CNN for image-based sign-alphabet recognition \cite{jayaprasad2025}; the present study instead treats the model as a frozen black box and edits its input." Do not say Grad-CAM (the abstract says only XAI). Do not say it supports any finding. | 05_discussion.tex, Limitations, as a note that our probe is behavioural and attribution-style analysis is future work; or acknowledgements/prior-work line | jayaprasad2025 |
| 7 (spare) | ACCEPT-WITH-REWRITE (tangential; generic UAV review) | "Motion blur and low light are listed among the hard imaging conditions for learned detectors in a recent review of UAV obstacle and aircraft detection \cite{randieri2025}." | 01_introduction.tex or 03_method.tex near the invariance motivation | randieri2025 |

Reviewer remarks to keep honest: (a) a referee will see #2, #3, #4, #7 as padding; keep each to one clause, do not build any argument on them. (b) #1 is the only citation that supports an argument; even it is by analogy. (c) #3 and #5 should not appear to be evidence that VAD systems detect physics violations. (d) Do not claim anything about V-JEPA's relation to these papers' methods.

### Corrected bibtex (changes only)

```
@inproceedings{amrutha2020,
  author    = {Amrutha, C. V. and Jyotsna, C. and Amudha, J.},
  title     = {Deep Learning Approach for Suspicious Activity Detection from Surveillance Video},
  booktitle = {2020 2nd International Conference on Innovative Mechanisms for Industry Applications (ICIMIA)},
  pages     = {335--339},
  year      = {2020},
  doi       = {10.1109/ICIMIA48430.2020.9074920}
}
@article{kandacharam2025,   % unchanged; add month = sep if the style wants it
  author  = {Kandacharam, Sneha and Rajathilagam, B. and Vasudevan, Shriram K.},
  title   = {Dual Encoder-Decoder-Encoder with Adversarial Training for Unsupervised Traffic Accident Detection in Surveillance Videos},
  journal = {Journal of Visualized Experiments},
  number  = {223},
  year    = {2025},
  doi     = {10.3791/68731}
}
@article{anjali2026,   % UNVERIFIED: given/family split and full names; no volume yet (early access)
  author  = {Anjali, S. and Don, S.},
  title   = {Explainable Video Anomaly Detection Using Video Masked Autoencoders and Convolutional {LSTM}},
  journal = {IEEE Open Journal of the Computer Society},
  pages   = {1--12},
  year    = {2026},
  doi     = {10.1109/OJCS.2026.3737277}
}
@inproceedings{jayaprasad2025,   % UNVERIFIED: third author's full name; record says "Anjali T"
  author    = {Jayaprasad, Vidyasree and Menon, Anand Rodriguez and Anjali, T.},
  title     = {Towards Inclusive {AI}: {EfficientNet}-based Recognition of Sign Language Alphabets},
  booktitle = {2025 5th International Conference on Evolutionary Computing and Mobile Sustainable Networks (ICECMSN)},
  pages     = {220--225},
  year      = {2025},
  publisher = {IEEE},
  doi       = {10.1109/ICECMSN68058.2025.11382596}
}
@article{randieri2025,
  author  = {Randieri, Cristian and Ganesh, Sai Venkata and Raj, Rayappa David Amar and Yanamala, Rama Muni Reddy and Pallakonda, Archana and Napoli, Christian},
  title   = {Aerial Autonomy Under Adversity: Advances in Obstacle and Aircraft Detection Techniques for Unmanned Aerial Vehicles},
  journal = {Drones},
  volume  = {9},
  number  = {8},
  pages   = {549},
  year    = {2025},
  doi     = {10.3390/drones9080549}
}
```
#1 and #2 bibtex verified unchanged.

### Count

Strict ACCEPT (no rewrite needed): 0. ACCEPT-WITH-REWRITE: 7 (#1-#7), of which #5 is conditional on a human reading the abstract and #6 is a self-citation. REJECT: 0. Six Amrita citations are therefore available (#1, #2, #3, #4, #6 plus #5 after the abstract check, with #7 as spare), but only #1 does real argumentative work.
