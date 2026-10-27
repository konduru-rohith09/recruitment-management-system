import { useCallback, useEffect, useState } from 'react'
import './App.css'

const API_URL = (
  import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'
).replace(/\/$/, '')
async function apiRequest(url, options = {}) {
  const response = await fetch(url, {
    ...options,
    headers: {
      Accept: 'application/json',
      ...(options.body ? { 'Content-Type': 'application/json' } : {}),
      ...options.headers,
    },
  })

  const text = await response.text()
  let data = null

  try {
    data = text ? JSON.parse(text) : null
  } catch {
    data = text
  }

  if (!response.ok) {
    const detail =
      typeof data === 'object' && data !== null
        ? data.detail ?? data.message ?? JSON.stringify(data)
        : data
    throw new Error(detail || `Request failed (${response.status})`)
  }

  return data
}

const INTERVIEW_ROUNDS = [
  'HR',
  'TECHNICAL',
  'SYSTEM_DESIGN',
  'BEHAVIORAL',
  'EXECUTIVE',
]

const INTERVIEW_STATUSES = [
  'SCHEDULED',
  'COMPLETED',
  'CANCELLED',
  'RESCHEDULED',
]

const RECOMMENDATIONS = [
  'STRONG_HIRE',
  'HIRE',
  'NO_HIRE',
  'STRONG_NO_HIRE',
]

const OFFER_STATUSES = [
  'DRAFT',
  'PENDING_APPROVAL',
  'APPROVED',
  'ISSUED',
  'ACCEPTED',
  'REJECTED',
  'WITHDRAWN',
  'EXPIRED',
]

const emptyRequisitionForm = {
  title: '',
  department_id: '',
  hiring_manager_id: '',
  min_salary: '',
  max_salary: '',
  headcount: '1',
  min_experience_years: '0',
  currency: 'USD',
  location: 'Remote',
  required_skill_ids_text: '',
}

const emptyInterviewForm = {
  application_id: '',
  round_number: '1',
  round_type: 'TECHNICAL',
  scheduled_start: '',
  scheduled_end: '',
  interviewer_ids: '',
}

const emptyFeedbackForm = {
  interview_id: '',
  interviewer_id: '',
  technical_rating: '3',
  communication_rating: '3',
  problem_solving_rating: '3',
  recommendation: 'HIRE',
  notes: '',
}

const emptyOfferForm = {
  application_id: '',
  base_salary: '',
  sign_on_bonus: '0',
  equity_shares: '0',
  currency: 'INR',
  approver_id: '',
}

const emptyOfferActionForm = {
  offer_id: '',
  approver_id: '',
  approval_status: 'APPROVED',
  comments: '',
  expiry_days: '7',
  actor: 'OFFER_COORDINATOR',
  decision: 'ACCEPTED',
  decision_actor: 'CANDIDATE',
  reason: '',
}

function formatDate(value) {
  if (!value) return '—'
  const date = new Date(value)
  return Number.isNaN(date.getTime())
    ? String(value)
    : date.toLocaleString()
}

function formatLabel(value) {
  return String(value ?? 'Unknown')
    .replaceAll('_', ' ')
    .replace(/\b\w/g, (letter) => letter.toUpperCase())
}

function Field({ label, children }) {
  return <label className="field-label">{label}{children}</label>
}

function Message({ error, success }) {
  return (
    <>
      {error && <div className="error-banner"><p>{String(error)}</p></div>}
      {success && <div className="success-banner">{success}</div>}
    </>
  )
}

function SectionHeading({ title, subtitle, onRefresh }) {
  return (
    <div className="section-heading">
      <div>
        <h2>{title}</h2>
        <p>{subtitle}</p>
      </div>
      {onRefresh && (
        <button type="button" className="secondary-button" onClick={onRefresh}>
          ↻ Refresh
        </button>
      )}
    </div>
  )
}

function App() {
  const [activePage, setActivePage] = useState('Overview')

  // Dashboard
  const [health, setHealth] = useState(null)
  const [metrics, setMetrics] = useState(null)
  const [anomalies, setAnomalies] = useState([])
  const [dashboardLoading, setDashboardLoading] = useState(true)
  const [dashboardError, setDashboardError] = useState('')

  // Applications
  const [applications, setApplications] = useState([])
  const [applicationTotal, setApplicationTotal] = useState(0)
  const [applicationsLoading, setApplicationsLoading] = useState(false)
  const [applicationsError, setApplicationsError] = useState('')
  const [applicationSearch, setApplicationSearch] = useState('')
  const [stageFilter, setStageFilter] = useState('ALL')
  // Candidates
  
  // Candidates
  const [candidates, setCandidates] = useState([])
  const [candidateTotal, setCandidateTotal] = useState(0)
  const [candidatesLoading, setCandidatesLoading] = useState(false)
  const [candidatesError, setCandidatesError] = useState('')
  const [candidateSearch, setCandidateSearch] = useState('')

  // Requisitions
  const [requisitions, setRequisitions] = useState([])
  const [requisitionTotal, setRequisitionTotal] = useState(0)
  const [requisitionsLoading, setRequisitionsLoading] = useState(false)
  const [requisitionsError, setRequisitionsError] = useState('')
  const [requisitionSearch, setRequisitionSearch] = useState('')
  const [requisitionStatus, setRequisitionStatus] = useState('ALL')
  const [requisitionForm, setRequisitionForm] = useState(emptyRequisitionForm)
  const [requisitionMessage, setRequisitionMessage] = useState('')
  const [requisitionFormError, setRequisitionFormError] = useState('')
  const [savingRequisition, setSavingRequisition] = useState(false)

  // Interviews
  const [interviews, setInterviews] = useState([])
  const [interviewTotal, setInterviewTotal] = useState(0)
  const [interviewsLoading, setInterviewsLoading] = useState(false)
  const [interviewsError, setInterviewsError] = useState('')
  const [interviewStatus, setInterviewStatus] = useState('ALL')
  const [interviewSearch, setInterviewSearch] = useState('')
  const [interviewForm, setInterviewForm] = useState(emptyInterviewForm)
  const [feedbackForm, setFeedbackForm] = useState(emptyFeedbackForm)
  const [interviewMessage, setInterviewMessage] = useState('')
  const [interviewFormError, setInterviewFormError] = useState('')
  const [savingInterview, setSavingInterview] = useState(false)
  const [savingFeedback, setSavingFeedback] = useState(false)
  const [feedbackMessage, setFeedbackMessage] = useState('')
  const [feedbackError, setFeedbackError] = useState('')

  // Offers
  const [offers, setOffers] = useState([])
  const [offerTotal, setOfferTotal] = useState(0)
  const [offersLoading, setOffersLoading] = useState(false)
  const [offersError, setOffersError] = useState('')
  const [offerStatus, setOfferStatus] = useState('ALL')
  const [offerSearch, setOfferSearch] = useState('')
  const [offerForm, setOfferForm] = useState(emptyOfferForm)
  const [approvalForm, setApprovalForm] = useState({ offer_id: '', approver_id: '', approval_status: 'APPROVED', comments: '' })
  const [issueForm, setIssueForm] = useState({ offer_id: '', expiry_days: '7', actor: 'OFFER_COORDINATOR' })
  const [decisionForm, setDecisionForm] = useState({ offer_id: '', decision: 'ACCEPTED', decision_actor: 'CANDIDATE', reason: '' })
  const [offerMessage, setOfferMessage] = useState('')
  const [offerFormError, setOfferFormError] = useState('')
  const [offerActionMessage, setOfferActionMessage] = useState('')
  const [offerActionError, setOfferActionError] = useState('')
  const [savingOffer, setSavingOffer] = useState(false)
  const [offerActionLoading, setOfferActionLoading] = useState('')

  const loadDashboard = useCallback(async () => {
    try {
      setDashboardLoading(true)
      setDashboardError('')

      const [healthData, metricsData, anomaliesData] = await Promise.all([
        apiRequest(`${API_URL}/health`),
        apiRequest(`${API_URL}/metrics`),
        apiRequest(`${API_URL}/anomalies`),
      ])

      setHealth(healthData)
      setMetrics(metricsData)

      setAnomalies(
        Array.isArray(anomaliesData)
          ? anomaliesData
          : anomaliesData?.items ?? anomaliesData?.anomalies ?? [],
      )
    } catch (error) {
      setDashboardError(
        `${error.message}. Check that the backend is running at ${API_URL}.`,
      )
    } finally {
      setDashboardLoading(false)
    }
  }, [])

  
  const loadCandidates = useCallback(async () => {
    try {
      setCandidatesLoading(true)
      setCandidatesError('')

      const params = new URLSearchParams({
        skip: '0',
        limit: '100',
      })

      if (candidateSearch.trim()) {
        params.set('search', candidateSearch.trim())
      }

      const data = await apiRequest(
        `${API_URL}/candidates?${params.toString()}`,
      )

      setCandidates(data?.items ?? [])
      setCandidateTotal(data?.total ?? 0)
    } catch (error) {
      setCandidatesError(error.message)
    } finally {
      setCandidatesLoading(false)
    }
  }, [candidateSearch])


  const loadApplications = useCallback(async () => {
    try {
      setApplicationsLoading(true)
      setApplicationsError('')
      const data = await apiRequest(
        `${API_URL}/applications?skip=0&limit=100`,
      )
      setApplications(data?.items ?? [])
      setApplicationTotal(data?.total ?? 0)
    } catch (error) {
      setApplicationsError(error.message)
    } finally {
      setApplicationsLoading(false)
    }
  }, [])

  const loadRequisitions = useCallback(async () => {
    try {
      setRequisitionsLoading(true)
      setRequisitionsError('')

      const params = new URLSearchParams({ skip: '0', limit: '100' })
      if (requisitionStatus !== 'ALL') {
        params.set('status', requisitionStatus)
      }

      const data = await apiRequest(
        `${API_URL}/requisitions?${params.toString()}`,
      )
      setRequisitions(data?.items ?? [])
      setRequisitionTotal(data?.total ?? 0)
    } catch (error) {
      setRequisitionsError(error.message)
    } finally {
      setRequisitionsLoading(false)
    }
  }, [requisitionStatus])

  const loadInterviews = useCallback(async () => {
    try {
      setInterviewsLoading(true)
      setInterviewsError('')

      const params = new URLSearchParams({ skip: '0', limit: '100' })
      if (interviewStatus !== 'ALL') {
        params.set('status', interviewStatus)
      }

      const data = await apiRequest(
        `${API_URL}/interviews?${params.toString()}`,
      )
      setInterviews(data?.items ?? [])
      setInterviewTotal(data?.total ?? 0)
    } catch (error) {
      setInterviewsError(error.message)
    } finally {
      setInterviewsLoading(false)
    }
  }, [interviewStatus])

  const loadOffers = useCallback(async () => {
    try {
      setOffersLoading(true)
      setOffersError('')

      const params = new URLSearchParams({ skip: '0', limit: '100' })
      if (offerStatus !== 'ALL') {
        params.set('status', offerStatus)
      }

      const data = await apiRequest(`${API_URL}/offers?${params.toString()}`)
      setOffers(data?.items ?? [])
      setOfferTotal(data?.total ?? 0)
    } catch (error) {
      setOffersError(error.message)
    } finally {
      setOffersLoading(false)
    }
  }, [offerStatus])

 
useEffect(() => {
  loadDashboard()
  loadApplications()
}, [loadDashboard, loadApplications])

useEffect(() => {
  if (activePage === 'Candidates') loadCandidates()
}, [activePage, loadCandidates])

useEffect(() => {
  if (activePage === 'Job Requisitions') loadRequisitions()
}, [activePage, loadRequisitions])

useEffect(() => {
  if (activePage === 'Interviews') loadInterviews()
}, [activePage, loadInterviews])

useEffect(() => {
  if (activePage === 'Offers') loadOffers()
}, [activePage, loadOffers])

function navigate(page) {
  setActivePage(page)
  if (page === 'Overview' || page === 'Anomalies') loadDashboard()
}


  // Requisition actions
  async function createRequisition(event) {
    event.preventDefault()
    setRequisitionFormError('')
    setRequisitionMessage('')

    const minSalary = Number(requisitionForm.min_salary)
    const maxSalary = Number(requisitionForm.max_salary)
    const departmentId = Number(requisitionForm.department_id)
    const headcount = Number(requisitionForm.headcount)
    const experience = Number(requisitionForm.min_experience_years)

    if (
      !requisitionForm.title.trim() ||
      !requisitionForm.hiring_manager_id.trim() ||
      !Number.isInteger(departmentId) ||
      departmentId < 1 ||
      requisitionForm.min_salary === '' ||
      requisitionForm.max_salary === '' ||
      !Number.isFinite(minSalary) ||
      !Number.isFinite(maxSalary) ||
      minSalary < 0 ||
      maxSalary < minSalary ||
      !Number.isInteger(headcount) ||
      headcount < 1 ||
      !Number.isFinite(experience) ||
      experience < 0
    ) {
      setRequisitionFormError(
        'Check the required fields, department ID, salary range, headcount, and experience.',
      )
      return
    }

    const skillText = requisitionForm.required_skill_ids_text.trim()
    const skillIds = skillText
      ? skillText.split(',').map((value) => Number(value.trim()))
      : null

    if (
      skillIds &&
      (skillIds.some((id) => !Number.isInteger(id) || id < 1) ||
        new Set(skillIds).size !== skillIds.length)
    ) {
      setRequisitionFormError(
        'Skill IDs must be unique positive whole numbers separated by commas.',
      )
      return
    }

    try {
      setSavingRequisition(true)
      await apiRequest(`${API_URL}/requisitions`, {
        method: 'POST',
        body: JSON.stringify({
          title: requisitionForm.title.trim(),
          department_id: departmentId,
          hiring_manager_id: requisitionForm.hiring_manager_id.trim(),
          min_salary: minSalary,
          max_salary: maxSalary,
          headcount,
          min_experience_years: experience,
          currency: requisitionForm.currency.toUpperCase(),
          location: requisitionForm.location.trim() || 'Remote',
          required_skill_ids: skillIds,
        }),
      })

      setRequisitionForm(emptyRequisitionForm)
      setRequisitionMessage('Job requisition created successfully.')
      await loadRequisitions()
    } catch (error) {
      setRequisitionFormError(error.message)
    } finally {
      setSavingRequisition(false)
    }
  }

  async function changeRequisitionStatus(item, action) {
    const id = item.requisition_id
    let url

    if (action === 'open') {
      const approver = window.prompt('Enter the approver ID:')
      if (!approver?.trim()) return
      url = `${API_URL}/requisitions/${encodeURIComponent(id)}/open?approver_id=${encodeURIComponent(approver.trim())}`
    } else {
      if (!window.confirm(`Close requisition ${id}?`)) return
      const actor = window.prompt('Enter the closing actor:', 'HR_ADMIN')
      if (!actor?.trim()) return
      url = `${API_URL}/requisitions/${encodeURIComponent(id)}/close?actor=${encodeURIComponent(actor.trim())}`
    }

    try {
      setRequisitionsError('')
      await apiRequest(url, { method: 'POST' })
      await loadRequisitions()
    } catch (error) {
      setRequisitionsError(error.message)
    }
  }

  // Interview actions
  async function scheduleInterview(event) {
    event.preventDefault()
    setInterviewFormError('')
    setInterviewMessage('')

    const start = new Date(interviewForm.scheduled_start)
    const end = new Date(interviewForm.scheduled_end)
    const interviewerIds = interviewForm.interviewer_ids
      .split(',')
      .map((id) => id.trim())
      .filter(Boolean)

    if (!interviewForm.application_id.trim()) {
      setInterviewFormError('Application ID is required.')
      return
    }

    if (
      !Number.isInteger(Number(interviewForm.round_number)) ||
      Number(interviewForm.round_number) < 1
    ) {
      setInterviewFormError('Round number must be a positive integer.')
      return
    }

    if (
      !interviewForm.scheduled_start ||
      !interviewForm.scheduled_end ||
      Number.isNaN(start.getTime()) ||
      Number.isNaN(end.getTime()) ||
      start >= end
    ) {
      setInterviewFormError('Enter valid start and end times; end must be later than start.')
      return
    }

    if (!interviewerIds.length) {
      setInterviewFormError('Enter at least one interviewer ID.')
      return
    }

    if (new Set(interviewerIds).size !== interviewerIds.length) {
      setInterviewFormError('Duplicate interviewer IDs are not allowed.')
      return
    }

    try {
      setSavingInterview(true)
      await apiRequest(`${API_URL}/interviews`, {
        method: 'POST',
        body: JSON.stringify({
          application_id: interviewForm.application_id.trim(),
          round_number: Number(interviewForm.round_number),
          round_type: interviewForm.round_type,
          scheduled_start: start.toISOString(),
          scheduled_end: end.toISOString(),
          interviewer_ids: interviewerIds,
        }),
      })

      setInterviewForm(emptyInterviewForm)
      setInterviewMessage('Interview scheduled successfully.')
      await loadInterviews()
    } catch (error) {
      setInterviewFormError(error.message)
    } finally {
      setSavingInterview(false)
    }
  }

  async function submitFeedback(event) {
    event.preventDefault()
    setFeedbackError('')
    setFeedbackMessage('')

    if (
      !feedbackForm.interview_id.trim() ||
      !feedbackForm.interviewer_id.trim() ||
      feedbackForm.notes.trim().length < 5
    ) {
      setInterviewFormError(
        'Enter an interview ID, interviewer ID, and at least five characters of feedback.',
      )
      return
    }

    try {
      setSavingFeedback(true)
      await apiRequest(
        `${API_URL}/interviews/${encodeURIComponent(feedbackForm.interview_id.trim())}/feedback`,
        {
          method: 'POST',
          body: JSON.stringify({
            interviewer_id: feedbackForm.interviewer_id.trim(),
            technical_rating: Number(feedbackForm.technical_rating),
            communication_rating: Number(feedbackForm.communication_rating),
            problem_solving_rating: Number(feedbackForm.problem_solving_rating),
            recommendation: feedbackForm.recommendation,
            notes: feedbackForm.notes.trim(),
          }),
        },
      )

      setFeedbackMessage('Feedback submitted successfully.')
      setFeedbackForm((previous) => ({ ...previous, notes: '' }))
    } catch (error) {
      setFeedbackError(error.message || 'Feedback submission failed. Please try again.')
    } finally {
      setSavingFeedback(false)
    }
  }

  // Offer actions
  async function createOffer(event) {
    event.preventDefault()
    setOfferFormError('')
    setOfferMessage('')

    const salary = Number(offerForm.base_salary)
    const bonus = Number(offerForm.sign_on_bonus)
    const equity = Number(offerForm.equity_shares)

    if (
      !offerForm.application_id.trim() ||
      !Number.isFinite(salary) ||
      salary <= 0 ||
      !Number.isFinite(bonus) ||
      bonus < 0 ||
      !Number.isInteger(equity) ||
      equity < 0
    ) {
      setOfferFormError('Enter a valid application ID, positive base salary, non-negative bonus, and whole-number equity.')
      return
    }

    try {
      setSavingOffer(true)
      await apiRequest(`${API_URL}/offers`, {
        method: 'POST',
        body: JSON.stringify({
          application_id: offerForm.application_id.trim(),
          base_salary: salary,
          sign_on_bonus: bonus,
          equity_shares: equity,
          currency: offerForm.currency.toUpperCase(),
          approver_id: offerForm.approver_id.trim() || null,
        }),
      })

      setOfferForm(emptyOfferForm)
      setOfferMessage('Offer created successfully.')
      await loadOffers()
    } catch (error) {
      setOfferFormError(error.message)
    } finally {
      setSavingOffer(false)
    }
  }

  async function approveOffer(event) {
    event.preventDefault()
    setOfferActionError('')
    setOfferActionMessage('')

    if (!approvalForm.offer_id.trim() || !approvalForm.approver_id.trim()) {
      setOfferActionError('Offer ID and approver ID are required.')
      return
    }

    setOfferActionLoading('approve')
    try {
      await apiRequest(
        `${API_URL}/offers/${encodeURIComponent(approvalForm.offer_id.trim())}/approve`,
        {
          method: 'POST',
          body: JSON.stringify({
            approver_id: approvalForm.approver_id.trim(),
            status: approvalForm.approval_status,
            comments: approvalForm.comments.trim() || null,
          }),
        },
      )
      setOfferActionMessage('Offer approval action completed successfully.')
      await loadOffers()
    } catch (error) {
      setOfferActionError(error.message || 'Offer approval failed.')
    } finally {
      setOfferActionLoading('')
    }
  }

  async function issueOffer(event) {
    event.preventDefault()
    setOfferActionError('')
    setOfferActionMessage('')

    if (!issueForm.offer_id.trim()) {
      setOfferActionError('Offer ID is required.')
      return
    }

    const days = Number(issueForm.expiry_days)
    if (!Number.isInteger(days) || days < 1 || days > 30) {
      setOfferActionError('Expiry must be between 1 and 30 days.')
      return
    }

    setOfferActionLoading('issue')
    try {
      const params = new URLSearchParams({
        expiry_days: String(days),
        actor: issueForm.actor.trim() || 'OFFER_COORDINATOR',
      })

      await apiRequest(
        `${API_URL}/offers/${encodeURIComponent(issueForm.offer_id.trim())}/issue?${params}`,
        { method: 'POST' },
      )
      setOfferActionMessage('Offer issued successfully.')
      await loadOffers()
    } catch (error) {
      setOfferActionError(error.message || 'Offer issuance failed.')
    } finally {
      setOfferActionLoading('')
    }
  }

  async function recordOfferDecision(event) {
    event.preventDefault()
    setOfferActionError('')
    setOfferActionMessage('')

    if (!decisionForm.offer_id.trim()) {
      setOfferActionError('Offer ID is required.')
      return
    }

    setOfferActionLoading('decision')
    try {
      await apiRequest(
        `${API_URL}/offers/${encodeURIComponent(decisionForm.offer_id.trim())}/decision`,
        {
          method: 'POST',
          body: JSON.stringify({
            decision: decisionForm.decision,
            actor: decisionForm.decision_actor.trim() || 'CANDIDATE',
            reason: decisionForm.reason.trim() || null,
          }),
        },
      )
      setOfferActionMessage('Candidate decision recorded successfully.')
      await loadOffers()
    } catch (error) {
      setOfferActionError(error.message || 'Recording candidate decision failed.')
    } finally {
      setOfferActionLoading('')
    }
  }

  // Corrected: /metrics returns nested objects, not top-level numeric values.
  const numericMetrics = metrics
    ? [
        ['total_requisitions', metrics.overview?.total_requisitions],
        ['total_applications', metrics.overview?.total_applications],
        ['total_interviews', metrics.overview?.total_interviews],
        ['total_offers', metrics.overview?.total_offers],
        ['screening_pass_rate_pct', metrics.screening?.screening_pass_rate_pct],
        ['average_screening_score', metrics.screening?.average_screening_score],
        ['interview_completion_rate_pct', metrics.interviews?.interview_completion_rate_pct],
        ['offer_acceptance_rate_pct', metrics.offers?.offer_acceptance_rate_pct],
        ['total_anomalies', metrics.anomalies?.total_count],
      ].filter(([, value]) => typeof value === 'number' && Number.isFinite(value))
    : []

  const stages = [...new Set(applications.map((item) => item.current_stage).filter(Boolean))]

  const filteredApplications = applications.filter((item) => {
    const query = applicationSearch.trim().toLowerCase()
    const matches = [
      item.application_id,
      item.candidate_id,
      item.requisition_id,
      item.current_stage,
    ].some((value) => String(value ?? '').toLowerCase().includes(query))

    return matches && (stageFilter === 'ALL' || item.current_stage === stageFilter)
  })

  const filteredRequisitions = requisitions.filter((item) =>
    [
      item.requisition_id,
      item.title,
      item.department_id,
      item.hiring_manager_id,
      item.location,
      item.status,
    ].some((value) =>
      String(value ?? '').toLowerCase().includes(requisitionSearch.trim().toLowerCase()),
    ),
  )

  const filteredInterviews = interviews.filter((item) =>
    [
      item.interview_id,
      item.application_id,
      item.round_type,
      item.status,
    ].some((value) =>
      String(value ?? '').toLowerCase().includes(interviewSearch.trim().toLowerCase()),
    ),
  )

  const filteredOffers = offers.filter((item) =>
    [
      item.offer_id,
      item.application_id,
      item.status,
    ].some((value) =>
      String(value ?? '').toLowerCase().includes(offerSearch.trim().toLowerCase()),
    ),
  )

  const navItems = [
    'Overview',
    'Candidates',
    'Job Requisitions',
    'Interviews',
    'Offers',
    'Anomalies',
  ]

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon">Y</div>
          <div>
            <h2>YottaFlex</h2>
            <span>Recruitment Platform</span>
          </div>
        </div>

        <p className="nav-heading">WORKSPACE</p>

        <nav className="navigation">
          {navItems.map((page) => (
            <button
              key={page}
              type="button"
              className={`nav-link ${activePage === page ? 'active' : ''}`}
              onClick={() => navigate(page)}
            >
              <span>
                {{
                  Overview: '▦',
                  Candidates: '♙',
                  'Job Requisitions': '▤',
                  Interviews: '▣',
                  Offers: '✉',
                  Anomalies: '⚠',
                }[page]}
              </span>
              {page}
            </button>
          ))}
        </nav>

        <div className="sidebar-footer">
          <span className={`status-dot ${health?.status === 'UP' ? 'online' : ''}`} />
          <div>
            <strong>Backend API</strong>
            <small>
              {health?.status === 'UP'
                ? 'Connected'
                : dashboardLoading
                  ? 'Connecting…'
                  : 'Disconnected'}
            </small>
          </div>
        </div>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <div>
            <p className="eyebrow">RECRUITMENT MANAGEMENT</p>
            <h1>{activePage}</h1>
            <p className="subtitle">
              {{
                Overview: 'Monitor your recruitment operations in one place.',
                Candidates: 'Search applications and track candidate progress.',
                'Job Requisitions': 'Create, search, open, and close hiring requisitions.',
                Interviews: 'Schedule interviews and submit interviewer feedback.',
                Offers: 'Create offers, manage approvals, and record candidate decisions.',
                Anomalies: 'Review potential workflow and compliance issues.',
              }[activePage]}
            </p>
          </div>

          <div className={`connection-badge ${health?.status === 'UP' ? 'connected' : 'disconnected'}`}>
            <span className="status-dot" />
            {health?.status === 'UP' ? 'API Connected' : 'API Disconnected'}
          </div>
        </header>

        {dashboardError && <Message error={dashboardError} />}

        {/* OVERVIEW */}
        {activePage === 'Overview' && (
          <>
            <section className="welcome-card">
              <div>
                <span className="welcome-label">RECRUITMENT OVERVIEW</span>
                <h2>Your hiring operations, at a glance.</h2>
                <p>Monitor recruitment metrics and workflow anomalies.</p>
              </div>
              <div className="welcome-symbol">↗</div>
            </section>

            <section className="section">
              <SectionHeading
                title="Key Metrics"
                subtitle="Values returned by your backend API"
                onRefresh={loadDashboard}
              />

              {dashboardLoading ? (
                <div className="panel">Loading dashboard data…</div>
              ) : numericMetrics.length ? (
                <div className="metrics-grid">
                  {numericMetrics.map(([key, value]) => (
                    <article className="metric-card" key={key}>
                      <div className="metric-top">
                        <span className="metric-icon">▦</span>
                        <span className="metric-indicator">LIVE</span>
                      </div>
                      <p className="metric-label">{formatLabel(key)}</p>
                      <h3>
                        {key.endsWith('_pct')
                          ? `${Number(value).toFixed(2).replace(/\.?0+$/, '')}%`
                          : key === 'average_screening_score'
                            ? Number(value).toFixed(2)
                            : Number(value).toLocaleString()}
                      </h3>
                    </article>
                  ))}
                </div>
              ) : (
                <div className="panel">No numeric metrics returned from /metrics.</div>
              )}
            </section>

            <section className="section">
              <SectionHeading
                title="Recruitment Modules"
                subtitle="Open a module to manage its records"
              />
              <div className="modules-grid">
                {navItems.filter((name) => name !== 'Overview' && name !== 'Anomalies').map((name) => (
                  <button
                    type="button"
                    className="module-card module-button"
                    key={name}
                    onClick={() => navigate(name)}
                  >
                    <span className="module-icon">▦</span>
                    <h3>{name}</h3>
                    <p>Open the {name.toLowerCase()} module.</p>
                    <span className="module-label">Open module →</span>
                  </button>
                ))}
              </div>
            </section>
          </>
        )}

{/* CANDIDATES */}
{activePage === 'Candidates' && (
  <section className="section">
    <SectionHeading
      title="Candidate Directory"
      subtitle={`${candidateTotal.toLocaleString()} total candidates`}
      onRefresh={loadCandidates}
    />

    <Message error={candidatesError} />

    <div className="filters">
      <input
        type="search"
        value={candidateSearch}
        onChange={(event) => setCandidateSearch(event.target.value)}
        placeholder="Search candidate ID, name, email or location..."
      />
    </div>

    <div className="table-container">
      <table>
        <thead>
          <tr>
            <th>Candidate ID</th>
            <th>Name</th>
            <th>Email</th>
            <th>Phone</th>
            <th>Location</th>
            <th>Experience (years)</th>
          </tr>
        </thead>

        <tbody>
          {candidatesLoading ? (
            <tr>
              <td colSpan="6" className="empty-state">
                Loading candidates...
              </td>
            </tr>
          ) : candidates.length > 0 ? (
            candidates.map((item) => (
              <tr key={item.candidate_id}>
                <td>{item.candidate_id}</td>
                <td>{item.first_name} {item.last_name}</td>
                <td>{item.email}</td>
                <td>{item.phone}</td>
                <td>{item.location}</td>
                <td>
                  {Number(item.total_experience_years ?? 0).toFixed(1)}
                </td>
              </tr>
            ))
          ) : (
            <tr>
              <td colSpan="6" className="empty-state">
                No matching candidates found.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  </section>
)}

        {/* JOB REQUISITIONS */}
        {activePage === 'Job Requisitions' && (
          <>
            <section className="section">
              <SectionHeading
                title="Create Job Requisition"
                subtitle="Add a hiring request to the recruitment database"
                onRefresh={loadRequisitions}
              />
              <Message error={requisitionFormError} success={requisitionMessage} />

              <form className="panel requisition-form" onSubmit={createRequisition}>
                <div className="form-grid">
                  <Field label="Job Title *">
                    <input required minLength={2} maxLength={150} value={requisitionForm.title} onChange={(e) => setRequisitionForm({ ...requisitionForm, title: e.target.value })} />
                  </Field>
                  <Field label="Department ID *">
                    <input required type="number" min="1" step="1" value={requisitionForm.department_id} onChange={(e) => setRequisitionForm({ ...requisitionForm, department_id: e.target.value })} />
                  </Field>
                  <Field label="Hiring Manager ID *">
                    <input required value={requisitionForm.hiring_manager_id} onChange={(e) => setRequisitionForm({ ...requisitionForm, hiring_manager_id: e.target.value })} />
                  </Field>
                  <Field label="Location">
                    <input value={requisitionForm.location} onChange={(e) => setRequisitionForm({ ...requisitionForm, location: e.target.value })} />
                  </Field>
                  <Field label="Minimum Salary *">
                    <input required type="number" min="0" step="0.01" value={requisitionForm.min_salary} onChange={(e) => setRequisitionForm({ ...requisitionForm, min_salary: e.target.value })} />
                  </Field>
                  <Field label="Maximum Salary *">
                    <input required type="number" min="0" step="0.01" value={requisitionForm.max_salary} onChange={(e) => setRequisitionForm({ ...requisitionForm, max_salary: e.target.value })} />
                  </Field>
                  <Field label="Currency">
                    <select value={requisitionForm.currency} onChange={(e) => setRequisitionForm({ ...requisitionForm, currency: e.target.value })}>
                      {['USD', 'INR', 'EUR', 'GBP'].map((value) => <option key={value}>{value}</option>)}
                    </select>
                  </Field>
                  <Field label="Headcount">
                    <input type="number" min="1" step="1" value={requisitionForm.headcount} onChange={(e) => setRequisitionForm({ ...requisitionForm, headcount: e.target.value })} />
                  </Field>
                  <Field label="Minimum Experience (years)">
                    <input type="number" min="0" step="0.5" value={requisitionForm.min_experience_years} onChange={(e) => setRequisitionForm({ ...requisitionForm, min_experience_years: e.target.value })} />
                  </Field>
                  <Field label="Required Skill IDs">
                    <input value={requisitionForm.required_skill_ids_text} onChange={(e) => setRequisitionForm({ ...requisitionForm, required_skill_ids_text: e.target.value })} placeholder="Optional: 1, 2, 3" />
                  </Field>
                </div>
                <p className="form-hint">Use existing department, manager, and skill IDs from your database.</p>
                <div className="form-actions">
                  <button className="primary-button" disabled={savingRequisition}>{savingRequisition ? 'Creating…' : 'Create Requisition'}</button>
                  <button type="button" className="secondary-button" onClick={() => setRequisitionForm(emptyRequisitionForm)}>Clear Form</button>
                </div>
              </form>
            </section>

            <section className="section">
              <SectionHeading title="Job Requisitions" subtitle={`${requisitionTotal} records returned by the API`} />
              <div className="filters">
                <input type="search" value={requisitionSearch} onChange={(e) => setRequisitionSearch(e.target.value)} placeholder="Search title, ID, manager or location…" />
                <select value={requisitionStatus} onChange={(e) => setRequisitionStatus(e.target.value)}>
                  <option value="ALL">All statuses</option>
                  {['DRAFT', 'PENDING_APPROVAL', 'OPEN', 'FILLED', 'CLOSED', 'CANCELLED'].map((value) => <option key={value}>{value}</option>)}
                </select>
              </div>
              <Message error={requisitionsError} />
              <div className="table-container">
                <table>
                  <thead>
                    <tr><th>ID</th><th>Job Title</th><th>Department</th><th>Manager</th><th>Location</th><th>Salary Range</th><th>Headcount</th><th>Status</th><th>Actions</th></tr>
                  </thead>
                  <tbody>
                    {requisitionsLoading ? (
                      <tr><td colSpan="9" className="empty-state">Loading requisitions…</td></tr>
                    ) : filteredRequisitions.length ? filteredRequisitions.map((item) => {
                      const status = String(item.status ?? '').toUpperCase()
                      return (
                        <tr key={item.requisition_id}>
                          <td>{item.requisition_id}</td>
                          <td>{item.title}</td>
                          <td>{item.department_id}</td>
                          <td>{item.hiring_manager_id}</td>
                          <td>{item.location}</td>
                          <td>{item.currency} {Number(item.min_salary).toLocaleString()} – {Number(item.max_salary).toLocaleString()}</td>
                          <td>{item.headcount}</td>
                          <td><span className="table-status">{formatLabel(status)}</span></td>
                          <td>
                            <div className="requisition-actions">
                              {status !== 'OPEN' && status !== 'CLOSED' && <button type="button" className="small-action" onClick={() => changeRequisitionStatus(item, 'open')}>Open</button>}
                              {status === 'OPEN' && <button type="button" className="small-action danger-action" onClick={() => changeRequisitionStatus(item, 'close')}>Close</button>}
                            </div>
                          </td>
                        </tr>
                      )
                    }) : <tr><td colSpan="9" className="empty-state">No matching requisitions found.</td></tr>}
                  </tbody>
                </table>
              </div>
            </section>
          </>
        )}

        {/* INTERVIEWS */}
        {activePage === 'Interviews' && (
          <>
            <section className="section">
              <SectionHeading title="Schedule Interview" subtitle="Schedule a round for an existing application" onRefresh={loadInterviews} />
              <Message error={interviewFormError} success={interviewMessage} />
              <form className="panel requisition-form" onSubmit={scheduleInterview}>
                <div className="form-grid">
                  <Field label="Application ID *">
                    <input required value={interviewForm.application_id} onChange={(e) => setInterviewForm({ ...interviewForm, application_id: e.target.value })} />
                  </Field>
                  <Field label="Round Number *">
                    <input required type="number" min="1" step="1" value={interviewForm.round_number} onChange={(e) => setInterviewForm({ ...interviewForm, round_number: e.target.value })} />
                  </Field>
                  <Field label="Round Type *">
                    <select value={interviewForm.round_type} onChange={(e) => setInterviewForm({ ...interviewForm, round_type: e.target.value })}>
                      {INTERVIEW_ROUNDS.map((value) => <option key={value}>{value}</option>)}
                    </select>
                  </Field>
                  <Field label="Interviewer IDs *">
                    <input required value={interviewForm.interviewer_ids} onChange={(e) => setInterviewForm({ ...interviewForm, interviewer_ids: e.target.value })} placeholder="ID-001, ID-002" />
                  </Field>
                  <Field label="Start Date and Time *">
                    <input required type="datetime-local" value={interviewForm.scheduled_start} onChange={(e) => setInterviewForm({ ...interviewForm, scheduled_start: e.target.value })} />
                  </Field>
                  <Field label="End Date and Time *">
                    <input required type="datetime-local" value={interviewForm.scheduled_end} onChange={(e) => setInterviewForm({ ...interviewForm, scheduled_end: e.target.value })} />
                  </Field>
                </div>
                <p className="form-hint">Enter existing application and interviewer IDs. Separate multiple interviewer IDs with commas.</p>
                <div className="form-actions">
                  <button className="primary-button" disabled={savingInterview}>{savingInterview ? 'Scheduling…' : 'Schedule Interview'}</button>
                </div>
              </form>
            </section>

            <section className="section">
              <SectionHeading title="Interview Records" subtitle={`${interviewTotal} records returned by the API`} />
              <div className="filters">
                <input type="search" value={interviewSearch} onChange={(e) => setInterviewSearch(e.target.value)} placeholder="Search interview or application ID…" />
                <select value={interviewStatus} onChange={(e) => setInterviewStatus(e.target.value)}>
                  <option value="ALL">All statuses</option>
                  {INTERVIEW_STATUSES.map((value) => <option key={value}>{value}</option>)}
                </select>
              </div>
              <Message error={interviewsError} />
              <div className="table-container">
                <table>
                  <thead>
                    <tr><th>Interview ID</th><th>Application ID</th><th>Round</th><th>Type</th><th>Start</th><th>End</th><th>Status</th><th>Action</th></tr>
                  </thead>
                  <tbody>
                    {interviewsLoading ? <tr><td colSpan="8" className="empty-state">Loading interviews…</td></tr> :
                      filteredInterviews.length ? filteredInterviews.map((item) => (
                        <tr key={item.interview_id}>
                          <td>{item.interview_id}</td>
                          <td>{item.application_id}</td>
                          <td>{item.round_number}</td>
                          <td>{item.round_type}</td>
                          <td>{formatDate(item.scheduled_start)}</td>
                          <td>{formatDate(item.scheduled_end)}</td>
                          <td><span className="table-status">{formatLabel(item.status)}</span></td>
                          <td><button type="button" className="small-action" onClick={() => setFeedbackForm({ ...feedbackForm, interview_id: item.interview_id })}>Give Feedback</button></td>
                        </tr>
                      )) : <tr><td colSpan="8" className="empty-state">No matching interviews found.</td></tr>}
                  </tbody>
                </table>
              </div>
            </section>

            <section className="section">
              <SectionHeading title="Submit Interview Feedback" subtitle="Record ratings and a recommendation" />
              <Message error={feedbackError} success={feedbackMessage} />
              <form className="panel requisition-form" onSubmit={submitFeedback}>
                <div className="form-grid">
                  <Field label="Interview ID *">
                    <input required value={feedbackForm.interview_id} onChange={(e) => setFeedbackForm({ ...feedbackForm, interview_id: e.target.value })} />
                  </Field>
                  <Field label="Interviewer ID *">
                    <input required value={feedbackForm.interviewer_id} onChange={(e) => setFeedbackForm({ ...feedbackForm, interviewer_id: e.target.value })} />
                  </Field>
                  {[
                    ['technical_rating', 'Technical Rating'],
                    ['communication_rating', 'Communication Rating'],
                    ['problem_solving_rating', 'Problem-Solving Rating'],
                  ].map(([name, label]) => (
                    <Field key={name} label={`${label} (1–5) *`}>
                      <select value={feedbackForm[name]} onChange={(e) => setFeedbackForm({ ...feedbackForm, [name]: e.target.value })}>
                        {[1, 2, 3, 4, 5].map((value) => <option key={value}>{value}</option>)}
                      </select>
                    </Field>
                  ))}
                  <Field label="Recommendation *">
                    <select value={feedbackForm.recommendation} onChange={(e) => setFeedbackForm({ ...feedbackForm, recommendation: e.target.value })}>
                      {RECOMMENDATIONS.map((value) => <option key={value}>{value}</option>)}
                    </select>
                  </Field>
                  <Field label="Feedback Notes *">
                    <textarea required minLength="5" value={feedbackForm.notes} onChange={(e) => setFeedbackForm({ ...feedbackForm, notes: e.target.value })} />
                  </Field>
                </div>
                <div className="form-actions">
                  <button className="primary-button" disabled={savingFeedback}>{savingFeedback ? 'Submitting…' : 'Submit Feedback'}</button>
                </div>
              </form>
            </section>
          </>
        )}

        {/* OFFERS */}
        {activePage === 'Offers' && (
          <>
            <section className="section">
              <SectionHeading title="Create Offer" subtitle="Create a compensation offer for an existing application" onRefresh={loadOffers} />
              <Message error={offerFormError} success={offerMessage} />
              <form className="panel requisition-form" onSubmit={createOffer}>
                <div className="form-grid">
                  <Field label="Application ID *">
                    <input required value={offerForm.application_id} onChange={(e) => setOfferForm({ ...offerForm, application_id: e.target.value })} />
                  </Field>
                  <Field label="Base Salary *">
                    <input required type="number" min="0.01" step="0.01" value={offerForm.base_salary} onChange={(e) => setOfferForm({ ...offerForm, base_salary: e.target.value })} />
                  </Field>
                  <Field label="Sign-on Bonus">
                    <input type="number" min="0" step="0.01" value={offerForm.sign_on_bonus} onChange={(e) => setOfferForm({ ...offerForm, sign_on_bonus: e.target.value })} />
                  </Field>
                  <Field label="Equity Shares">
                    <input type="number" min="0" step="1" value={offerForm.equity_shares} onChange={(e) => setOfferForm({ ...offerForm, equity_shares: e.target.value })} />
                  </Field>
                  <Field label="Currency">
                    <select value={offerForm.currency} onChange={(e) => setOfferForm({ ...offerForm, currency: e.target.value })}>
                      {['INR', 'USD', 'EUR', 'GBP'].map((value) => <option key={value}>{value}</option>)}
                    </select>
                  </Field>
                  <Field label="Approver ID (if required)">
                    <input value={offerForm.approver_id} onChange={(e) => setOfferForm({ ...offerForm, approver_id: e.target.value })} />
                  </Field>
                </div>
                <div className="form-actions">
                  <button className="primary-button" disabled={savingOffer}>{savingOffer ? 'Creating…' : 'Create Offer'}</button>
                </div>
              </form>
            </section>

            <section className="section">
              <SectionHeading title="Offer Records" subtitle={`${offerTotal} records returned by the API`} />
              <div className="filters">
                <input type="search" value={offerSearch} onChange={(e) => setOfferSearch(e.target.value)} placeholder="Search offer or application ID…" />
                <select value={offerStatus} onChange={(e) => setOfferStatus(e.target.value)}>
                  <option value="ALL">All statuses</option>
                  {OFFER_STATUSES.map((value) => <option key={value}>{value}</option>)}
                </select>
              </div>
              <Message error={offersError} />
              <div className="table-container">
                <table>
                  <thead>
                    <tr><th>Offer ID</th><th>Application ID</th><th>Base Salary</th><th>Bonus</th><th>Equity</th><th>Status</th><th>Issued</th><th>Expires</th></tr>
                  </thead>
                  <tbody>
                    {offersLoading ? <tr><td colSpan="8" className="empty-state">Loading offers…</td></tr> :
                      filteredOffers.length ? filteredOffers.map((item) => (
                        <tr key={item.offer_id}>
                          <td>{item.offer_id}</td>
                          <td>{item.application_id}</td>
                          <td>{item.currency} {Number(item.base_salary).toLocaleString()}</td>
                          <td>{item.currency} {Number(item.sign_on_bonus).toLocaleString()}</td>
                          <td>{item.equity_shares}</td>
                          <td><span className="table-status">{formatLabel(item.status)}</span></td>
                          <td>{formatDate(item.issued_at)}</td>
                          <td>{formatDate(item.expires_at)}</td>
                        </tr>
                      )) : <tr><td colSpan="8" className="empty-state">No matching offers found.</td></tr>}
                  </tbody>
                </table>
              </div>
            </section>

            <section className="section">
              <SectionHeading title="Offer Workflow Actions" subtitle="Approve, issue, or record a candidate decision" />
              <Message error={offerActionError} success={offerActionMessage} />

              <form className="panel requisition-form" onSubmit={approveOffer}>
                <h3>Approve or Reject an Offer</h3>
                <div className="form-grid">
                  <Field label="Offer ID *">
                    <input required value={approvalForm.offer_id} onChange={(e) => setApprovalForm({ ...approvalForm, offer_id: e.target.value })} />
                  </Field>
                  <Field label="Approver ID *">
                    <input required value={approvalForm.approver_id} onChange={(e) => setApprovalForm({ ...approvalForm, approver_id: e.target.value })} />
                  </Field>
                  <Field label="Approval Status *">
                    <select value={approvalForm.approval_status} onChange={(e) => setApprovalForm({ ...approvalForm, approval_status: e.target.value })}>
                      {['APPROVED', 'REJECTED', 'PENDING'].map((value) => <option key={value}>{value}</option>)}
                    </select>
                  </Field>
                  <Field label="Comments">
                    <input value={approvalForm.comments} onChange={(e) => setApprovalForm({ ...approvalForm, comments: e.target.value })} />
                  </Field>
                </div>
                <div className="form-actions"><button type="submit" className="primary-button" disabled={offerActionLoading !== ''}>{offerActionLoading === 'approve' ? 'Submitting...' : 'Submit Approval'}</button></div>
              </form>

              <form className="panel requisition-form" onSubmit={issueOffer}>
                <h3>Issue an Approved Offer</h3>
                <div className="form-grid">
                  <Field label="Offer ID *">
                    <input required value={issueForm.offer_id} onChange={(e) => setIssueForm({ ...issueForm, offer_id: e.target.value })} />
                  </Field>
                  <Field label="Expiry (days)">
                    <input required type="number" min="1" max="30" value={issueForm.expiry_days} onChange={(e) => setIssueForm({ ...issueForm, expiry_days: e.target.value })} />
                  </Field>
                  <Field label="Actor">
                    <input value={issueForm.actor} onChange={(e) => setIssueForm({ ...issueForm, actor: e.target.value })} />
                  </Field>
                </div>
                <div className="form-actions"><button type="submit" className="primary-button" disabled={offerActionLoading !== ''}>{offerActionLoading === 'issue' ? 'Issuing...' : 'Issue Offer'}</button></div>
              </form>

              <form className="panel requisition-form" onSubmit={recordOfferDecision}>
                <h3>Record Candidate Decision</h3>
                <div className="form-grid">
                  <Field label="Offer ID *">
                    <input required value={decisionForm.offer_id} onChange={(e) => setDecisionForm({ ...decisionForm, offer_id: e.target.value })} />
                  </Field>
                  <Field label="Decision *">
                    <select value={decisionForm.decision} onChange={(e) => setDecisionForm({ ...decisionForm, decision: e.target.value })}>
                      {['ACCEPTED', 'REJECTED', 'WITHDRAWN'].map((value) => <option key={value}>{value}</option>)}
                    </select>
                  </Field>
                  <Field label="Actor">
                    <input value={decisionForm.decision_actor} onChange={(e) => setDecisionForm({ ...decisionForm, decision_actor: e.target.value })} />
                  </Field>
                  <Field label="Reason">
                    <input value={decisionForm.reason} onChange={(e) => setDecisionForm({ ...decisionForm, reason: e.target.value })} />
                  </Field>
                </div>
                <div className="form-actions"><button type="submit" className="primary-button" disabled={offerActionLoading !== ''}>{offerActionLoading === 'decision' ? 'Recording...' : 'Record Decision'}</button></div>
              </form>
            </section>
          </>
        )}

        {/* ANOMALIES */}
        {activePage === 'Anomalies' && (
          <section className="section">
            <SectionHeading
              title="Workflow Anomalies"
              subtitle="Potential workflow and compliance issues reported by the API"
            />
            <div className="table-container">
              <table>
                <thead>
                  <tr><th>Issue ID</th><th>Issue Type</th><th>Details</th><th>Severity</th></tr>
                </thead>
                <tbody>
                  {anomalies.length ? anomalies.map((item, index) => (
                    <tr key={item.issue_id ?? index}>
                      <td>{item.issue_id ?? '—'}</td>
                      <td>{item.issue_type ?? '—'}</td>
                      <td>{item.explanation ?? item.message ?? item.description ?? '—'}</td>
                      <td><span className="table-status">{item.severity ?? '—'}</span></td>
                    </tr>
                  )) : <tr><td colSpan="4" className="empty-state">No anomaly records returned.</td></tr>}
                </tbody>
              </table>
            </div>
          </section>
        )}

        <footer className="footer">
          <span>YottaFlex Recruitment Management System</span>
          <span>React + FastAPI</span>
        </footer>
      </main>
    </div>
  )
}

export default App