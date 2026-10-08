import { useEffect, useState } from 'react'
import './App.css'

const API_URL = 'http://127.0.0.1:8000'
const HISTORY_LIMIT = 10

function App() {
  const [prompt, setPrompt] = useState('')
  const [response, setResponse] = useState('')
  const [referenceAnswer, setReferenceAnswer] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [history, setHistory] = useState([])
  const [historyLoading, setHistoryLoading] = useState(true)
  const [historyError, setHistoryError] = useState('')
  const [historyOffset, setHistoryOffset] = useState(0)
  const [historyTotal, setHistoryTotal] = useState(0)
  const [analytics, setAnalytics] = useState(null)
  const [analyticsLoading, setAnalyticsLoading] = useState(true)
  const [analyticsError, setAnalyticsError] = useState('')

  const fetchAnalytics = async () => {
    setAnalyticsLoading(true)
    setAnalyticsError('')

    try {
      const apiResponse = await fetch(`${API_URL}/analytics`)
      const data = await apiResponse.json()

      if (!apiResponse.ok) {
        throw new Error(
          typeof data.detail === 'string'
            ? data.detail
            : 'Unable to load analytics.',
        )
      }

      setAnalytics(data)
    } catch (requestError) {
      setAnalyticsError(
        requestError.message ||
          'Unable to connect to the analytics API.',
      )
    } finally {
      setAnalyticsLoading(false)
    }
  }

  const fetchHistory = async (offset = historyOffset) => {
    setHistoryLoading(true)
    setHistoryError('')

    try {
      const apiResponse = await fetch(
        `${API_URL}/evaluations?limit=${HISTORY_LIMIT}&offset=${offset}`,
      )

      const data = await apiResponse.json()

      if (!apiResponse.ok) {
        throw new Error(
          typeof data.detail === 'string'
            ? data.detail
            : 'Unable to load evaluation history.',
        )
      }

      setHistory(data.items || [])
      setHistoryTotal(data.total || 0)
      setHistoryOffset(data.offset || 0)
    } catch (requestError) {
      setHistoryError(
        requestError.message ||
          'Unable to connect to the evaluation API.',
      )
    } finally {
      setHistoryLoading(false)
    }
  }

  useEffect(() => {
    fetchHistory(0)
    fetchAnalytics()
  }, [])

  const evaluateResponse = async (event) => {
    event.preventDefault()

    if (!prompt.trim() || !response.trim()) {
      setError('Prompt and response are required.')
      return
    }

    setLoading(true)
    setError('')
    setResult(null)

    try {
      const payload = {
        prompt: prompt.trim(),
        response: response.trim(),
      }

      if (referenceAnswer.trim()) {
        payload.reference_answer = referenceAnswer.trim()
      }

      const apiResponse = await fetch(`${API_URL}/evaluate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      })

      const data = await apiResponse.json()

      if (!apiResponse.ok) {
        throw new Error(
          typeof data.detail === 'string'
            ? data.detail
            : 'Evaluation failed.',
        )
      }

      setResult(data)
      setHistoryOffset(0)

      await Promise.all([
        fetchHistory(0),
        fetchAnalytics(),
      ])
    } catch (requestError) {
      setError(
        requestError.message ||
          'Unable to connect to the evaluation API.',
      )
    } finally {
      setLoading(false)
    }
  }

  const resetForm = () => {
    setPrompt('')
    setResponse('')
    setReferenceAnswer('')
    setResult(null)
    setError('')
  }

  const loadEvaluation = async (evaluationId) => {
    setHistoryError('')

    try {
      const apiResponse = await fetch(
        `${API_URL}/evaluations/${evaluationId}`,
      )

      const data = await apiResponse.json()

      if (!apiResponse.ok) {
        throw new Error(
          typeof data.detail === 'string'
            ? data.detail
            : 'Unable to load evaluation.',
        )
      }

      setResult(data)

      window.scrollTo({
        top: 0,
        behavior: 'smooth',
      })
    } catch (requestError) {
      setHistoryError(
        requestError.message ||
          'Unable to load the selected evaluation.',
      )
    }
  }

  const nextHistoryPage = () => {
    if (historyOffset + HISTORY_LIMIT < historyTotal) {
      fetchHistory(historyOffset + HISTORY_LIMIT)
    }
  }

  const previousHistoryPage = () => {
    if (historyOffset > 0) {
      fetchHistory(
        Math.max(0, historyOffset - HISTORY_LIMIT),
      )
    }
  }

  const formatDate = (timestamp) => {
    if (!timestamp) {
      return 'Unknown date'
    }

    return new Date(timestamp).toLocaleString()
  }

  const getScoreClass = (score) => {
    if (score === null || score === undefined) {
      return 'neutral'
    }

    if (score >= 80) {
      return 'good'
    }

    if (score >= 50) {
      return 'medium'
    }

    return 'bad'
  }

  return (
    <div className="app">
      <header className="header">
        <div className="brand">
          <div className="brand-mark">AI</div>

          <div>
            <h1>AI Evaluation Platform</h1>
            <p>LLM response evaluation and quality analysis</p>
          </div>
        </div>

        <div className="status">
          <span className="status-dot"></span>
          API Ready
        </div>
      </header>

      <main className="main">
        <section className="hero">
          <div>
            <span className="eyebrow">Evaluation Dashboard</span>

            <h2>Evaluate AI responses with confidence.</h2>

            <p>
              Compare deterministic evaluation with an LLM judge and
              inspect accuracy, relevance, completeness, and feedback.
            </p>
          </div>

          <div className="hero-stats">
            <div className="stat-card">
              <strong>2</strong>
              <span>Evaluation Methods</span>
            </div>

            <div className="stat-card">
              <strong>3</strong>
              <span>Quality Metrics</span>
            </div>

            <div className="stat-card">
              <strong>100</strong>
              <span>Maximum Score</span>
            </div>
          </div>
        </section>

        <section className="workspace">
          <form
            className="evaluation-form"
            onSubmit={evaluateResponse}
          >
            <div className="section-heading">
              <div>
                <span className="section-label">01</span>
                <h3>Evaluation Input</h3>
              </div>

              <button
                type="button"
                className="secondary-button"
                onClick={resetForm}
              >
                Clear
              </button>
            </div>

            <label htmlFor="prompt">Prompt</label>

            <textarea
              id="prompt"
              value={prompt}
              onChange={(event) => setPrompt(event.target.value)}
              placeholder="Enter the original prompt..."
              rows="5"
            />

            <label htmlFor="response">AI Response</label>

            <textarea
              id="response"
              value={response}
              onChange={(event) => setResponse(event.target.value)}
              placeholder="Enter the AI-generated response..."
              rows="7"
            />

            <label htmlFor="reference">
              Reference Answer
              <span className="optional">Optional</span>
            </label>

            <textarea
              id="reference"
              value={referenceAnswer}
              onChange={(event) =>
                setReferenceAnswer(event.target.value)
              }
              placeholder="Enter the expected or reference answer..."
              rows="7"
            />

            {error && <div className="error">{error}</div>}

            <button
              className="primary-button"
              type="submit"
              disabled={loading}
            >
              {loading ? 'Evaluating...' : 'Run Evaluation'}
            </button>
          </form>

          <section className="results">
            <div className="section-heading">
              <div>
                <span className="section-label">02</span>
                <h3>Evaluation Results</h3>
              </div>

              {result && (
                <span
                  className={
                    result.passed
                      ? 'result-badge pass'
                      : 'result-badge fail'
                  }
                >
                  {result.passed ? 'PASSED' : 'FAILED'}
                </span>
              )}
            </div>

            {!result && !loading && (
              <div className="empty-state">
                <div className="empty-icon">◎</div>
                <h4>No evaluation yet</h4>
                <p>
                  Submit a prompt and AI response to see evaluation
                  results here.
                </p>
              </div>
            )}

            {loading && (
              <div className="empty-state">
                <div className="loader"></div>
                <h4>Running evaluation</h4>
                <p>
                  The deterministic evaluator and local LLM judge are
                  processing the response.
                </p>
              </div>
            )}

            {result && (
              <div className="result-content">
                <div className="score-card">
                  <span>Overall Score</span>

                  <strong>
                    {result.score !== null
                      ? result.score.toFixed(2)
                      : 'N/A'}
                  </strong>

                  <small>/ 100</small>
                </div>

                <div className="metrics">
                  <div className="metric">
                    <span>Accuracy</span>

                    <strong>
                      {result.accuracy !== null
                        ? `${result.accuracy.toFixed(2)}%`
                        : 'N/A'}
                    </strong>
                  </div>

                  <div className="metric">
                    <span>Relevance</span>

                    <strong>
                      {result.relevance !== null
                        ? `${result.relevance.toFixed(2)}%`
                        : 'N/A'}
                    </strong>
                  </div>

                  <div className="metric">
                    <span>Completeness</span>

                    <strong>
                      {result.completeness !== null
                        ? `${result.completeness.toFixed(2)}%`
                        : 'N/A'}
                    </strong>
                  </div>
                </div>

                <div className="feedback-card">
                  <span>Deterministic Feedback</span>
                  <p>{result.feedback}</p>
                </div>

                {result.llm_judge && (
                  <div className="llm-card">
                    <div className="card-header">
                      <div>
                        <span>LLM Judge</span>
                        <h4>Qwen 3:8B Evaluation</h4>
                      </div>

                      <strong>
                        {result.llm_judge.overall_score.toFixed(2)}
                      </strong>
                    </div>

                    <div className="llm-metrics">
                      <div>
                        <span>Accuracy</span>
                        <strong>
                          {result.llm_judge.accuracy.toFixed(2)}
                        </strong>
                      </div>

                      <div>
                        <span>Relevance</span>
                        <strong>
                          {result.llm_judge.relevance.toFixed(2)}
                        </strong>
                      </div>

                      <div>
                        <span>Completeness</span>
                        <strong>
                          {result.llm_judge.completeness.toFixed(2)}
                        </strong>
                      </div>
                    </div>

                    <p className="llm-feedback">
                      {result.llm_judge.feedback}
                    </p>
                  </div>
                )}

                {result.comparison && (
                  <div className="comparison-card">
                    <div className="card-header">
                      <div>
                        <span>Evaluation Comparison</span>
                        <h4>Deterministic vs LLM Judge</h4>
                      </div>

                      <strong>
                        {result.comparison.absolute_difference.toFixed(2)}
                      </strong>
                    </div>

                    <div className="comparison-grid">
                      <div>
                        <span>Deterministic</span>
                        <strong>
                          {result.comparison.deterministic_score.toFixed(
                            2,
                          )}
                        </strong>
                      </div>

                      <div>
                        <span>LLM Judge</span>
                        <strong>
                          {result.comparison.llm_score.toFixed(2)}
                        </strong>
                      </div>

                      <div>
                        <span>Difference</span>
                        <strong>
                          {result.comparison.score_difference > 0
                            ? '+'
                            : ''}
                          {result.comparison.score_difference.toFixed(
                            2,
                          )}
                        </strong>
                      </div>
                    </div>
                  </div>
                )}

                {result.matched_terms?.length > 0 && (
                  <div className="terms-card">
                    <span>Matched Terms</span>

                    <div className="terms">
                      {result.matched_terms.map((term) => (
                        <span key={term}>{term}</span>
                      ))}
                    </div>
                  </div>
                )}

                {result.missing_terms?.length > 0 && (
                  <div className="terms-card">
                    <span>Missing Terms</span>

                    <div className="terms missing">
                      {result.missing_terms.map((term) => (
                        <span key={term}>{term}</span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </section>
        </section>

        <section className="analytics-section">
          <div className="section-heading">
            <div>
              <span className="section-label">03</span>
              <h3>Analytics Overview</h3>
            </div>

            <button
              type="button"
              className="secondary-button"
              onClick={fetchAnalytics}
              disabled={analyticsLoading}
            >
              {analyticsLoading ? 'Loading...' : 'Refresh'}
            </button>
          </div>

          {analyticsError && (
            <div className="error">{analyticsError}</div>
          )}

          {analyticsLoading && !analytics && (
            <div className="analytics-loading">
              <div className="loader"></div>
              <h4>Loading analytics</h4>
              <p>Calculating evaluation performance metrics.</p>
            </div>
          )}

          {analytics && (
            <div className="analytics-grid">
              <div className="analytics-card">
                <span>Total Evaluations</span>
                <strong>{analytics.total_evaluations}</strong>
                <small>
                  {analytics.scored_evaluations} scored evaluations
                </small>
              </div>

              <div className="analytics-card">
                <span>Average Score</span>
                <strong>
                  {analytics.average_score.toFixed(2)}
                </strong>
                <small>Out of 100</small>
              </div>

              <div className="analytics-card">
                <span>Pass Rate</span>
                <strong>
                  {analytics.pass_rate.toFixed(1)}%
                </strong>
                <small>
                  {analytics.passed_evaluations} passed
                </small>
              </div>

              <div className="analytics-card">
                <span>Average Accuracy</span>
                <strong>
                  {analytics.average_accuracy.toFixed(1)}%
                </strong>
                <small>Deterministic evaluator</small>
              </div>

              <div className="analytics-card">
                <span>Average Relevance</span>
                <strong>
                  {analytics.average_relevance.toFixed(1)}%
                </strong>
                <small>Deterministic evaluator</small>
              </div>

              <div className="analytics-card">
                <span>Average Completeness</span>
                <strong>
                  {analytics.average_completeness.toFixed(1)}%
                </strong>
                <small>Deterministic evaluator</small>
              </div>

              <div className="analytics-card llm-analytics">
                <span>LLM Judge Average</span>
                <strong>
                  {analytics.average_llm_score.toFixed(2)}
                </strong>
                <small>
                  {analytics.llm_evaluations} LLM evaluations
                </small>
              </div>

              <div className="analytics-card comparison-analytics">
                <span>Deterministic vs LLM Difference</span>
                <strong>
                  {analytics.average_score_difference.toFixed(2)}
                </strong>
                <small>Average absolute difference</small>
              </div>
            </div>
          )}

          {analytics && (
            <div className="analytics-details">
              <div className="analytics-detail-card">
                <span>LLM Accuracy</span>
                <strong>
                  {analytics.average_llm_accuracy.toFixed(1)}%
                </strong>
              </div>

              <div className="analytics-detail-card">
                <span>LLM Relevance</span>
                <strong>
                  {analytics.average_llm_relevance.toFixed(1)}%
                </strong>
              </div>

              <div className="analytics-detail-card">
                <span>LLM Completeness</span>
                <strong>
                  {analytics.average_llm_completeness.toFixed(1)}%
                </strong>
              </div>

              <div className="analytics-detail-card">
                <span>Comparisons</span>
                <strong>
                  {analytics.comparison_evaluations}
                </strong>
              </div>
            </div>
          )}
        </section>

        <section className="history-section">
          <div className="section-heading">
            <div>
              <span className="section-label">04</span>
              <h3>Evaluation History</h3>
            </div>

            <button
              type="button"
              className="secondary-button"
              onClick={() => fetchHistory(0)}
              disabled={historyLoading}
            >
              {historyLoading ? 'Loading...' : 'Refresh'}
            </button>
          </div>

          {historyError && (
            <div className="error">{historyError}</div>
          )}

          {historyLoading && history.length === 0 && (
            <div className="history-empty">
              <div className="loader"></div>
              <h4>Loading evaluation history</h4>
              <p>Fetching saved evaluations from SQLite.</p>
            </div>
          )}

          {!historyLoading &&
            history.length === 0 &&
            !historyError && (
              <div className="history-empty">
                <div className="empty-icon">◷</div>
                <h4>No evaluation history</h4>
                <p>
                  Completed evaluations will appear here
                  automatically.
                </p>
              </div>
            )}

          {history.length > 0 && (
            <>
              <div className="history-list">
                {history.map((evaluation, index) => (
                  <article
                    className="history-item"
                    key={
                      evaluation.evaluation_id ||
                      `${evaluation.timestamp}-${index}`
                    }
                  >
                    <div className="history-main">
                      <div className="history-number">
                        {(historyOffset + index + 1)
                          .toString()
                          .padStart(2, '0')}
                      </div>

                      <div className="history-info">
                        <div className="history-title">
                          <h4>
                            Evaluation #
                            {evaluation.evaluation_id?.slice(
                              0,
                              8,
                            ) || 'Unknown'}
                          </h4>

                          <span
                            className={
                              evaluation.passed
                                ? 'history-status pass'
                                : evaluation.passed === false
                                  ? 'history-status fail'
                                  : 'history-status neutral'
                            }
                          >
                            {evaluation.passed === true
                              ? 'PASSED'
                              : evaluation.passed === false
                                ? 'FAILED'
                                : 'NO REFERENCE'}
                          </span>
                        </div>

                        <p>
                          {formatDate(evaluation.timestamp)}
                        </p>

                        <span className="history-method">
                          {evaluation.evaluation_method ||
                            'Evaluation'}
                        </span>
                      </div>
                    </div>

                    <div className="history-metrics">
                      <div>
                        <span>Score</span>

                        <strong
                          className={getScoreClass(
                            evaluation.score,
                          )}
                        >
                          {evaluation.score !== null &&
                          evaluation.score !== undefined
                            ? evaluation.score.toFixed(2)
                            : 'N/A'}
                        </strong>
                      </div>

                      <div>
                        <span>Accuracy</span>

                        <strong>
                          {evaluation.accuracy !== null &&
                          evaluation.accuracy !== undefined
                            ? `${evaluation.accuracy.toFixed(1)}%`
                            : 'N/A'}
                        </strong>
                      </div>

                      <div>
                        <span>Relevance</span>

                        <strong>
                          {evaluation.relevance !== null &&
                          evaluation.relevance !== undefined
                            ? `${evaluation.relevance.toFixed(1)}%`
                            : 'N/A'}
                        </strong>
                      </div>

                      <div>
                        <span>Completeness</span>

                        <strong>
                          {evaluation.completeness !== null &&
                          evaluation.completeness !== undefined
                            ? `${evaluation.completeness.toFixed(1)}%`
                            : 'N/A'}
                        </strong>
                      </div>
                    </div>

                    <button
                      type="button"
                      className="history-button"
                      onClick={() =>
                        loadEvaluation(
                          evaluation.evaluation_id,
                        )
                      }
                    >
                      View
                    </button>
                  </article>
                ))}
              </div>

              <div className="history-pagination">
                <span>
                  Showing {historyOffset + 1}–
                  {Math.min(
                    historyOffset + history.length,
                    historyTotal,
                  )}{' '}
                  of {historyTotal}
                </span>

                <div>
                  <button
                    type="button"
                    className="secondary-button"
                    onClick={previousHistoryPage}
                    disabled={
                      historyOffset === 0 ||
                      historyLoading
                    }
                  >
                    Previous
                  </button>

                  <button
                    type="button"
                    className="secondary-button"
                    onClick={nextHistoryPage}
                    disabled={
                      historyOffset + HISTORY_LIMIT >=
                        historyTotal ||
                      historyLoading
                    }
                  >
                    Next
                  </button>
                </div>
              </div>
            </>
          )}
        </section>
      </main>

      <footer className="footer">
        <span>AI Evaluation Platform</span>
        <span>
          FastAPI · React · SQLite · Qwen 3:8B
        </span>
      </footer>
    </div>
  )
}

export default App