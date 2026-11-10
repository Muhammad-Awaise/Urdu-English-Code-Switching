import type { ReactNode } from 'react'

const toc = [
  { id: 'summary', label: 'Executive summary' },
  { id: 'about', label: 'What the project is' },
  { id: 'objectives', label: 'Objectives' },
  { id: 'doing', label: 'What the system does' },
  { id: 'problem', label: 'Problem statement' },
  { id: 'why-hard', label: 'Why it is hard' },
  { id: 'example', label: 'Worked example' },
  { id: 'resolved', label: 'How it is resolved' },
  { id: 'policy', label: 'Detection policies' },
  { id: 'pipeline', label: 'End-to-end pipeline' },
  { id: 'modules', label: 'Application modules' },
  { id: 'models', label: 'Models & training' },
  { id: 'data', label: 'Data & annotation' },
  { id: 'research', label: 'Research workflow' },
  { id: 'constraints', label: 'Free / local constraints' },
  { id: 'limitations', label: 'Limitations' },
  { id: 'next', label: 'Where to go next' },
]

export default function AboutProject() {
  return (
    <div className="space-y-6 max-w-5xl">
      <header className="card overflow-hidden">
        <div
          className="px-6 py-8 text-white"
          style={{
            background: 'linear-gradient(135deg, #071526 0%, #0b1f3a 50%, #1e4fd6 140%)',
          }}
        >
          <div className="text-xs uppercase tracking-[0.2em] text-blue-200">Detailed project brief</div>
          <h2 className="brand-serif text-4xl mt-2">About this project</h2>
          <p className="mt-3 max-w-3xl text-blue-100/90 leading-relaxed">
            A full explanation of the Urdu–English Code-Switching Analyzer: the bilingual text
            problem it targets, what the platform does at each step, and how local free/open-source
            NLP and machine learning resolve that problem in a reproducible research workflow.
          </p>
        </div>
        <div className="px-6 py-4 flex flex-wrap gap-2 bg-[var(--card)]">
          {toc.map((item) => (
            <a
              key={item.id}
              href={`#${item.id}`}
              className="rounded-full border border-[var(--line)] bg-white px-3 py-1 text-xs text-[var(--royal)] hover:border-[var(--royal)]"
            >
              {item.label}
            </a>
          ))}
        </div>
      </header>

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <InfoCard label="Domain" value="Roman Urdu ↔ English code-switching" />
        <InfoCard label="Core task" value="Word-level language identification" />
        <InfoCard label="Output" value="Labels, highlights, CS status, metrics" />
        <InfoCard label="Constraint" value="Free, local, CPU-friendly, no paid APIs" />
      </section>

      <Section id="summary" title="1. Executive summary">
        <p>
          People frequently write messages that mix <strong>English</strong> and{' '}
          <strong>Roman Urdu</strong> in the same sentence, using the Latin alphabet for both.
          A system that only “detects language for the whole sentence” is not enough for research
          or product features that need to know <em>which words</em> belong to which language.
        </p>
        <p>
          This project builds a complete local research platform that:
        </p>
        <ul className="list-disc pl-5 space-y-1">
          <li>classifies every token as Roman Urdu, English, ambiguous, unknown, or other;</li>
          <li>visualizes the mix with color highlighting and analytics;</li>
          <li>detects code-switching with an explicit evidence policy;</li>
          <li>lets researchers create/annotate datasets and train classical ML models on CPU;</li>
          <li>stores experiments, evaluations, and research notes without paid cloud AI services.</li>
        </ul>
      </Section>

      <Section id="about" title="2. What this project is">
        <p>
          <strong>Project name:</strong> Urdu-English Code-Switching Analyzer
        </p>
        <p>
          <strong>Subtitle:</strong> Detecting Urdu and English in Mixed-Language Text
        </p>
        <p>
          It is an NLP research application, not a single-page demo. The backend is FastAPI with
          SQLite persistence. The frontend is a React research console. Machine learning uses
          Scikit-learn and Joblib locally. Optional deep learning is not required for the core
          workflow.
        </p>
        <p>
          The scientific center of the project is <strong>word-level language identification</strong>{' '}
          for Latin-script bilingual text, plus transparent measurement of whether a sentence is
          truly code-switched.
        </p>
      </Section>

      <Section id="objectives" title="3. Research and product objectives">
        <ol className="list-decimal pl-5 space-y-2">
          <li>
            Identify Roman Urdu and English words inside mixed sentences with per-token labels.
          </li>
          <li>
            Preserve uncertainty: keep ambiguous/unknown tokens instead of forcing false certainty.
          </li>
          <li>
            Detect code-switching only when both languages are reliably present.
          </li>
          <li>
            Enable dataset creation, annotation, cleaning, and reproducible train/validation/test splits.
          </li>
          <li>
            Train and compare free local classifiers (dictionary baseline, Logistic Regression,
            Linear SVM, Naive Bayes) on CPU.
          </li>
          <li>
            Evaluate with real held-out predictions, confusion matrices, and error inspection.
          </li>
          <li>
            Support research documentation: notes, methodology draft, literature stubs, experiment
            journal, and local report export.
          </li>
        </ol>
      </Section>

      <Section id="doing" title="4. What the system is doing (in practice)">
        <p>When a user analyzes text, the system performs these operations:</p>
        <ol className="list-decimal pl-5 space-y-2">
          <li>
            <strong>Ingest text</strong> — single sentence, multiple sentences, or a paragraph.
          </li>
          <li>
            <strong>Optional preprocessing</strong> — Unicode normalization, cleaning, whitespace
            cleanup, lowercase, repeated-character collapse, and configurable Roman Urdu spelling
            normalization (for example achha→acha, nahin→nahi), while keeping original text available.
          </li>
          <li>
            <strong>Tokenization</strong> — splits words and separates punctuation, numbers, URLs,
            mentions, hashtags, and emojis as special token kinds.
          </li>
          <li>
            <strong>Classification</strong> — each word receives a label from the active trained
            model, or from the dictionary baseline if no model is active.
          </li>
          <li>
            <strong>Explanation UI</strong> — tokens are highlighted; clicking a token shows label,
            confidence (when real probabilities exist), position, model version, and alternative
            suggestion when available.
          </li>
          <li>
            <strong>Analytics</strong> — counts, percentages, frequent words, language transitions,
            confidence distribution, ambiguous-word report, and sentence-level breakdown.
          </li>
          <li>
            <strong>Code-switching decision</strong> — YES / NO / INSUFFICIENT EVIDENCE according to
            the evidence policy below.
          </li>
        </ol>
      </Section>

      <Section id="problem" title="5. Problem statement (detailed)">
        <p>
          In bilingual digital communication, especially in Pakistan and diaspora communities,
          users often write Urdu using English letters (Roman Urdu) and insert English words in the
          same message. This is natural for chat, social media, reviews, emails, and student text.
        </p>
        <p>
          The core computational problem is:
        </p>
        <blockquote className="border-l-4 border-[var(--royal)] bg-[var(--royal-soft)] px-4 py-3 rounded-r-xl text-[var(--ink)]">
          Given a Latin-script sentence that may contain Roman Urdu, English, or both, assign a
          language label to each token and decide whether the sentence exhibits code-switching.
        </blockquote>
        <p>
          Whole-sentence language ID is insufficient because a “mixed” sentence still needs
          word-level boundaries for linguistic analysis, feature engineering, translation support,
          educational tools, and fair evaluation of bilingual models.
        </p>
        <p>
          Commercial hosted LLM APIs can sometimes guess labels, but they introduce cost, privacy
          risk, non-reproducible behavior, offline failure, and dependency on billing accounts.
          This project deliberately rejects that path and builds a free local alternative.
        </p>
      </Section>

      <Section id="why-hard" title="6. Why the problem is difficult">
        <ul className="list-disc pl-5 space-y-2">
          <li>
            <strong>Shared script:</strong> both languages appear in Latin characters, so Arabic-script
            detectors do not help for Roman Urdu.
          </li>
          <li>
            <strong>Lexical borrowing:</strong> English content words often sit inside Urdu grammar
            (“university”, “admission”, “apply”, “deadline”).
          </li>
          <li>
            <strong>Ambiguous short tokens:</strong> words like “to”, “so”, “me”, “in” can be English
            or Roman Urdu depending on context.
          </li>
          <li>
            <strong>Spelling variation:</strong> Roman Urdu has no single orthography (nahi/nahin,
            acha/achha, raha/rha).
          </li>
          <li>
            <strong>Context dependence:</strong> the same surface form may change meaning across
            sentences; pure token dictionaries can fail without sequence context.
          </li>
          <li>
            <strong>Data scarcity:</strong> freely licensed word-level Roman Urdu–English datasets are
            limited. The platform therefore includes annotation tools instead of inventing fake corpora
            or metrics.
          </li>
        </ul>
      </Section>

      <Section id="example" title="7. Worked example">
        <p>
          <strong>Input:</strong>
        </p>
        <pre className="rounded-xl bg-[var(--card)] p-4 text-sm overflow-x-auto">
Main university mein admission apply kar raha hoon.
        </pre>
        <p>
          <strong>Target word-level pattern (illustrative research labels):</strong>
        </p>
        <div className="overflow-x-auto">
          <table className="w-full text-sm border-collapse">
            <thead>
              <tr className="text-left border-b border-[var(--line)]">
                <th className="py-2 pr-3">Word</th>
                <th className="py-2">Classification</th>
              </tr>
            </thead>
            <tbody>
              {[
                ['Main', 'URDU_ROMAN'],
                ['university', 'ENGLISH'],
                ['mein', 'URDU_ROMAN'],
                ['admission', 'ENGLISH'],
                ['apply', 'ENGLISH'],
                ['kar', 'URDU_ROMAN'],
                ['raha', 'URDU_ROMAN'],
                ['hoon', 'URDU_ROMAN'],
              ].map(([w, l]) => (
                <tr key={w} className="border-b border-[var(--line)]/70">
                  <td className="py-2 pr-3 font-medium">{w}</td>
                  <td className="py-2">{l}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="mt-3">
          <strong>Expected analytical reading:</strong> Roman Urdu tokens and English tokens both
          appear with confidence → languages detected: Urdu and English → code-switching status:{' '}
          <strong>YES</strong>. Punctuation is labeled OTHER and does not count as a language token.
        </p>
        <p>
          In the live analyzer, labels always come from the currently selected/active classifier.
          The table above describes the intended linguistic target, not a fabricated benchmark score.
        </p>
      </Section>

      <Section id="resolved" title="8. How this project resolves the problem">
        <p>The resolution is layered: immediate baseline analysis, then data-driven improvement.</p>
        <h4 className="font-semibold text-[var(--ink)] mt-4">8.1 Immediate resolution (dictionary baseline)</h4>
        <ul className="list-disc pl-5 space-y-1">
          <li>Local Roman Urdu lexicon for common function/content words.</li>
          <li>Local English common-word lexicon.</li>
          <li>Explicit ambiguous list for high-overlap tokens.</li>
          <li>Unknown label when a word is absent from all lists.</li>
          <li>OTHER for non-word symbols and special tokens.</li>
        </ul>
        <p className="mt-2">
          This gives researchers a working analyzer on day one without waiting for model training.
        </p>

        <h4 className="font-semibold text-[var(--ink)] mt-4">8.2 Linguistic resolution (policies)</h4>
        <ul className="list-disc pl-5 space-y-1">
          <li>Do not force ambiguous words into Urdu or English.</li>
          <li>Do not claim code-switching when only one language is reliably found.</li>
          <li>Allow preprocessing on/off comparison so normalization side effects are visible.</li>
        </ul>

        <h4 className="font-semibold text-[var(--ink)] mt-4">8.3 Data resolution (annotation platform)</h4>
        <ul className="list-disc pl-5 space-y-1">
          <li>Import CSV / Excel / JSON / JSONL or enter sentences manually.</li>
          <li>Annotate tokens, mark uncertainty, filter unlabeled items, validate alignment issues.</li>
          <li>Clean empties with explicit actions (no silent deletion).</li>
          <li>Split into train/validation/test with reproducible seeds and duplicate grouping to reduce leakage.</li>
        </ul>

        <h4 className="font-semibold text-[var(--ink)] mt-4">8.4 Statistical resolution (local ML)</h4>
        <ul className="list-disc pl-5 space-y-1">
          <li>Character n-grams help capture Roman Urdu morphology and spelling variants.</li>
          <li>Word n-grams / TF-IDF capture lexical identity.</li>
          <li>Logistic Regression, Linear SVM, and Naive Bayes train on CPU and save joblib artifacts.</li>
          <li>Models are registered but never auto-overwrite the active production/inference model.</li>
        </ul>

        <h4 className="font-semibold text-[var(--ink)] mt-4">8.5 Scientific resolution (evaluation + research center)</h4>
        <ul className="list-disc pl-5 space-y-1">
          <li>Metrics come from real test predictions only.</li>
          <li>Confusion matrices and misclassified tokens support error analysis.</li>
          <li>Experiment records are created when training completes.</li>
          <li>Notes, methodology draft, literature entries, and local report exports support write-up.</li>
        </ul>
      </Section>

      <Section id="policy" title="9. Detection and labeling policies">
        <h4 className="font-semibold text-[var(--ink)]">Token labels</h4>
        <ul className="list-disc pl-5 space-y-1 mt-2">
          <li><strong>URDU_ROMAN</strong> — Romanized Urdu lexical item.</li>
          <li><strong>ENGLISH</strong> — English lexical item.</li>
          <li><strong>AMBIGUOUS</strong> — plausible in both / unclear without forcing a side.</li>
          <li><strong>UNKNOWN</strong> — not confidently identifiable from current resources.</li>
          <li><strong>OTHER</strong> — punctuation, numbers, URLs, mentions, emojis, symbols.</li>
        </ul>
        <h4 className="font-semibold text-[var(--ink)] mt-4">Code-switching statuses</h4>
        <ul className="list-disc pl-5 space-y-1 mt-2">
          <li>
            <strong>YES</strong> — both Urdu and English have enough reliable tokens (default: at least
            one confident token each).
          </li>
          <li>
            <strong>NO</strong> — exactly one language is reliably present.
          </li>
          <li>
            <strong>INSUFFICIENT EVIDENCE</strong> — too few reliable language tokens (for example only
            ambiguous/unknown/other content).
          </li>
        </ul>
        <p className="mt-2">
          Confidence thresholds are configurable in settings. Models without native probabilities do
          not invent fake confidence scores; calibrated probabilities are used only where supported.
        </p>
      </Section>

      <Section id="pipeline" title="10. End-to-end resolution pipeline">
        <ol className="list-decimal pl-5 space-y-2">
          <li>Analyze text with dictionary baseline to explore phenomena.</li>
          <li>Collect representative mixed sentences.</li>
          <li>Annotate word-level labels carefully; mark uncertain tokens.</li>
          <li>Validate dataset; clean empties; split 70/15/15 with a fixed seed.</li>
          <li>Compare preprocessing variants in the Preprocessing Lab.</li>
          <li>Train LogReg / Linear SVM / Naive Bayes locally on CPU.</li>
          <li>Inspect evaluation metrics, confusion matrix, and misclassifications.</li>
          <li>Activate a chosen model in the registry (manual activation only).</li>
          <li>Re-run analyzer; confirm model version appears on predictions.</li>
          <li>Record findings in Research Center and export reports locally.</li>
        </ol>
        <p className="mt-3">
          This loop converts a linguistic problem into measurable labels, reproducible experiments,
          and documented conclusions—without paid inference APIs.
        </p>
      </Section>

      <Section id="modules" title="11. Application modules and their role">
        <div className="overflow-x-auto">
          <table className="w-full text-sm border-collapse">
            <thead>
              <tr className="text-left border-b border-[var(--line)]">
                <th className="py-2 pr-3">Module</th>
                <th className="py-2">Purpose in resolving the problem</th>
              </tr>
            </thead>
            <tbody>
              {[
                ['Overview', 'Live dashboard of dataset and model progress from real stored data.'],
                ['About Project', 'Explains problem, solution, and research framing (this page).'],
                ['Text Analyzer', 'Primary inference UI: highlight, counts, CS status, analytics.'],
                ['Datasets', 'Import, validate, clean, split corpora used for training/evaluation.'],
                ['Annotation', 'Create gold word-level labels needed for supervised learning.'],
                ['Preprocessing Lab', 'Inspect how normalization changes tokens before modeling.'],
                ['Training Lab', 'Run local CPU training jobs with progress and cancellation.'],
                ['Evaluation', 'Compare models using real metrics and error examples.'],
                ['Model Registry', 'Activate/deactivate artifacts; prevent silent overwrite.'],
                ['Experiments', 'Track completed training runs and stored results.'],
                ['Research Center', 'Notes, literature stubs, methodology draft, report export.'],
                ['Settings', 'Local configuration; confirms zero paid-service dependency.'],
              ].map(([m, p]) => (
                <tr key={m} className="border-b border-[var(--line)]/70 align-top">
                  <td className="py-2 pr-3 font-medium whitespace-nowrap">{m}</td>
                  <td className="py-2 text-[var(--muted)]">{p}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Section>

      <Section id="models" title="12. Models and training strategy">
        <ul className="list-disc pl-5 space-y-2">
          <li>
            <strong>Dictionary baseline</strong> — explainable starting point; always available as fallback.
          </li>
          <li>
            <strong>TF-IDF + Logistic Regression</strong> — strong classical baseline with probabilities.
          </li>
          <li>
            <strong>TF-IDF + Linear SVM</strong> — margin-based classifier; calibration used when class
            counts allow real probability estimates.
          </li>
          <li>
            <strong>Naive Bayes</strong> — fast probabilistic baseline for comparison.
          </li>
        </ul>
        <p className="mt-3">
          Character n-grams are especially important for Roman Urdu because spelling variants often
          share character patterns even when full-word forms differ. Training runs in a background
          worker so the analyzer remains usable. Large jobs require explicit confirmation. GPU is
          optional and never mandatory.
        </p>
      </Section>

      <Section id="data" title="13. Data reality and annotation strategy">
        <p>
          The platform ships a small illustrative annotated sample only to verify the pipeline. It is
          <strong> not</strong> a research benchmark and must not be treated as one.
        </p>
        <p>
          If no suitable external open-license word-level dataset is available, researchers should
          build their own annotated set in the Annotation workspace. External datasets may be imported
          only after license and label-quality checks. The project does not scrape private conversations
          or use paid corpora.
        </p>
      </Section>

      <Section id="research" title="14. Research workflow supported by the app">
        <ul className="list-disc pl-5 space-y-2">
          <li>Formulate research questions around spelling variation, ambiguity, and CS detection policy.</li>
          <li>Document annotation guidelines and methodology in the Research Center (draft template included).</li>
          <li>Log experiments automatically after training completes; add manual observations.</li>
          <li>Export Markdown / DOCX / PDF reports locally with clear separation of draft vs actual results.</li>
          <li>Never invent citations or metrics; literature entries are manual and verified by the user.</li>
        </ul>
      </Section>

      <Section id="constraints" title="15. Free and local operating constraints">
        <ul className="list-disc pl-5 space-y-1">
          <li>No OpenAI / Gemini / Claude / paid Hugging Face inference.</li>
          <li>No required API keys or credit-card services for core functionality.</li>
          <li>All default training and inference run locally on CPU.</li>
          <li>Artifacts, datasets, notes, and reports are stored on local disk / SQLite.</li>
          <li>Large model weights are not auto-downloaded.</li>
        </ul>
      </Section>

      <Section id="limitations" title="16. Limitations (honest scope)">
        <ul className="list-disc pl-5 space-y-2">
          <li>Dictionary coverage is incomplete; UNKNOWN labels are expected for rare words.</li>
          <li>Token classifiers are mostly context-blind; some ambiguities need sequence models later.</li>
          <li>Roman Urdu normalization maps are helpful but not exhaustive or universally interchangeable.</li>
          <li>Sample data is too small for strong generalization claims.</li>
          <li>Free cloud hosts (if used later) may sleep, wipe ephemeral disks, or limit long training; local CPU remains the reliable training environment.</li>
        </ul>
      </Section>

      <Section id="next" title="17. Where to go next in the application">
        <ul className="list-disc pl-5 space-y-2">
          <li>
            <strong>Text Analyzer</strong> — paste mixed Roman Urdu/English text and inspect highlights.
          </li>
          <li>
            <strong>Annotation / Datasets</strong> — grow a trustworthy labeled corpus.
          </li>
          <li>
            <strong>Preprocessing Lab</strong> — compare normalized vs raw tokens before modeling.
          </li>
          <li>
            <strong>Training Lab → Evaluation → Model Registry</strong> — improve beyond the dictionary baseline with measured results.
          </li>
          <li>
            <strong>Research Center</strong> — keep the scientific narrative aligned with actual experiments.
          </li>
        </ul>
      </Section>
    </div>
  )
}

function InfoCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="card p-4">
      <div className="text-xs uppercase tracking-wide text-[var(--muted)]">{label}</div>
      <div className="mt-2 font-semibold leading-snug">{value}</div>
    </div>
  )
}

function Section({
  id,
  title,
  children,
}: {
  id: string
  title: string
  children: ReactNode
}) {
  return (
    <section id={id} className="card p-6 scroll-mt-6">
      <h3 className="brand-serif text-2xl text-[var(--navy)]">{title}</h3>
      <div className="mt-4 space-y-3 text-[15px] leading-relaxed text-[var(--muted)] [&_strong]:text-[var(--ink)]">
        {children}
      </div>
    </section>
  )
}
