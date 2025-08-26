'use client'
import React, { useState, useEffect } from 'react'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  ArcElement,
} from 'chart.js'
import { Bar, Radar, Doughnut } from 'react-chartjs-2'

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  ArcElement
)

// Fetch policy data from backend API (all policies, not just approved)
const fetchPolicyData = async () => {
  try {
    // Use NEXT_PUBLIC_API_URL from .env
    const baseUrl = process.env.NEXT_PUBLIC_API_URL || ''
    const apiUrl = `${baseUrl}/policy/all`
    const res = await fetch(apiUrl)
    if (!res.ok) throw new Error('Failed to fetch policy data')
    const result = await res.json()
    // The OpenAPI spec shows the response is { success, data, count }
    return result.data || []
  } catch (err) {
    console.error(err)
    return []
  }
}

// Fetch TEA scores from ai_policy_database_map_policies table
const fetchTeaScores = async () => {
  try {
    const baseUrl = process.env.NEXT_PUBLIC_API_URL || ''
    const apiUrl = `${baseUrl}/ai-analysis/tea-scores`
    const res = await fetch(apiUrl)
    if (!res.ok) {
      console.warn('TEA scores endpoint not available, falling back to calculated scores')
      return []
    }
    const result = await res.json()
    return result.data || []
  } catch (err) {
    console.error('Error fetching TEA scores:', err)
    return []
  }
}

// Country aggregation function
const getCountryAggregatedData = (policyData) => {
  const countryData = {}
  if (!policyData || !policyData.length) return []
  
  // Include all policies regardless of evaluation status for fallback
  policyData.forEach(policy => {
    if (!countryData[policy.country]) {
      countryData[policy.country] = {
        country: policy.country,
        countryCode: policy.countryCode,
        policies: [],
        totalPolicies: 0,
        avgTransparency: 0,
        avgExplainability: 0,
        avgAccountability: 0,
        avgTotalScore: 0,
        categories: {}
      }
    }
    countryData[policy.country].policies.push(policy)
    countryData[policy.country].totalPolicies++
    if (!countryData[policy.country].categories[policy.category]) {
      countryData[policy.country].categories[policy.category] = 0
    }
    countryData[policy.country].categories[policy.category]++
  })
  
  Object.keys(countryData).forEach(country => {
    const data = countryData[country]
    const policies = data.policies
    data.avgTransparency = policies.length ? (policies.reduce((sum, p) => sum + (p.transparencyScore ?? 0), 0) / policies.length) : 0
    data.avgExplainability = policies.length ? (policies.reduce((sum, p) => sum + (p.explainabilityScore ?? 0), 0) / policies.length) : 0
    data.avgAccountability = policies.length ? (policies.reduce((sum, p) => sum + (p.accountabilityScore ?? 0), 0) / policies.length) : 0
    data.avgTotalScore = policies.length ? (policies.reduce((sum, p) => sum + ((p.transparencyScore ?? 0) + (p.explainabilityScore ?? 0) + (p.accountabilityScore ?? 0)), 0) / policies.length) : 0
  })
  return Object.values(countryData).sort((a, b) => b.avgTotalScore - a.avgTotalScore)
}

// Helper function to merge TEA scores with policy data
const mergePolicyWithTeaScores = (submissions, teaScores) => {
  // Use TEA scores as the primary source since they contain evaluated policies with real scores
  console.log(`Processing ${teaScores.length} TEA scores from database`)
  
  const evaluatedPolicies = teaScores
    .filter(score => score.isEvaluated)
    .map(score => ({
      id: score.policyId,
      policyId: score.policyId,
      title: score.policyName || 'Unnamed Policy',
      country: score.country,
      category: score.policyArea,
      transparencyScore: parseInt(score.transparencyScore) || 0,
      explainabilityScore: parseInt(score.explainabilityScore) || 0,
      accountabilityScore: parseInt(score.accountabilityScore) || 0,
      totalScore: (parseInt(score.transparencyScore) || 0) + 
                 (parseInt(score.explainabilityScore) || 0) + 
                 (parseInt(score.accountabilityScore) || 0),
      isEvaluated: true,
      evaluationType: score.evaluationType,
      riskAssessment: score.riskAssessment,
      // For backward compatibility with existing UI components
      transparency: { score: parseInt(score.transparencyScore) || 0 },
      explainability: { score: parseInt(score.explainabilityScore) || 0 },
      accountability: { score: parseInt(score.accountabilityScore) || 0 }
    }))
  
  console.log(`Extracted ${evaluatedPolicies.length} evaluated policies with real TEA scores from database`)
  console.log('Sample policy:', evaluatedPolicies[0])
  
  return evaluatedPolicies
}

const evaluationCriteria = {
  transparency: [
    "Is the full policy document publicly accessible?",
    "Does the policy clearly list the stakeholders involved in its creation?", 
    "Was there public consultation or feedback collected?",
    "Does the policy provide open data or reporting on implementation?",
    "Are decision-making criteria or algorithms disclosed?"
  ],
  explainability: [
    "Does the policy require systems to provide human-interpretable outputs?",
    "Are explanations tailored to the audience (technical/non-technical)?",
    "Are the decision-making processes (e.g., risk assessments) documented?",
    "Are users informed about how AI decisions are made?",
    "Does the policy include guidance for explainability in deployment?"
  ],
  accountability: [
    "Does the policy assign responsibility for AI decisions or harm?",
    "Are there auditing or oversight mechanisms in place?",
    "Can individuals seek redress or appeal AI decisions?",
    "Is liability for misuse or errors clearly outlined?",
    "Is there a governing/regulatory body identified?"
  ]
}

function PolicyRanking({ setView }) {
  const [policyData, setPolicyData] = useState([])
  const [loading, setLoading] = useState(true)
  const [selectedView, setSelectedView] = useState('overview')
  // Track expanded state for each policy card (multiple can be expanded)
  const [expandedPolicies, setExpandedPolicies] = useState({})
  const [expandedCountry, setExpandedCountry] = useState(null)
  const [sortBy, setSortBy] = useState('totalScore')
  const [sortOrder, setSortOrder] = useState('desc')
  const [filterCategory, setFilterCategory] = useState('all')
  const [viewMode, setViewMode] = useState('policies') // 'policies' or 'countries'
  const [selectedPolicyArea, setSelectedPolicyArea] = useState(null) // For country comparison by policy area


  // State for full country and policy area lists
  const [fullCountries, setFullCountries] = useState([])
  const [fullPolicyAreas, setFullPolicyAreas] = useState([]) // array of objects

  // Fetch full country and policy area lists from backend using NEXT_PUBLIC_API_URL
  useEffect(() => {
    const fetchLists = async () => {
      try {
        const baseUrl = process.env.NEXT_PUBLIC_API_URL || ''
        const [countriesRes, areasRes] = await Promise.all([
          fetch(`${baseUrl}/countries`),
          fetch(`${baseUrl}/policy-areas`)
        ])
        const countriesData = countriesRes.ok ? await countriesRes.json() : { countries: [] }
        const areasData = areasRes.ok ? await areasRes.json() : { policy_areas: [] }
        setFullCountries(countriesData.countries || [])
        setFullPolicyAreas(areasData.policy_areas || []) // keep as objects
      } catch (err) {
        setFullCountries([])
        setFullPolicyAreas([])
      }
    }
    fetchLists()
  }, [])

  // Use full lists for dropdowns and charts
  const categories = ['all', ...fullPolicyAreas.map(a => a.name)]
  const categoryObjects = [{ id: 'all', name: 'All Categories' }, ...fullPolicyAreas]

  useEffect(() => {
    const loadData = async () => {
      setLoading(true)
      try {
        // Fetch both policy data and TEA scores
        const [policiesData, teaScoresData] = await Promise.all([
          fetchPolicyData(),
          fetchTeaScores()
        ])
        
        // Merge policies with TEA scores, filtering only evaluated policies
        const mergedData = mergePolicyWithTeaScores(policiesData, teaScoresData)
        setPolicyData(mergedData)
      } catch (error) {
        console.error('Error loading data:', error)
        setPolicyData([])
      }
      setLoading(false)
    }
    loadData()
  }, [])

  // Use robust country aggregation for countries view
  const countryData = getCountryAggregatedData(policyData)

  // Normalize category filtering
  const sortedPolicies = [...policyData]
    .filter(policy => {
      if (filterCategory === 'all') return true
      // Match by name or id
      const matchByName = policy.category && policy.category.trim().toLowerCase() === filterCategory.trim().toLowerCase()
      const matchById = categoryObjects.find(cat => cat.name === filterCategory)?.id && policy.categoryId === categoryObjects.find(cat => cat.name === filterCategory).id
      return matchByName || matchById
    })
    .sort((a, b) => {
      let aVal, bVal
      
      if (sortBy === 'totalScore') {
        aVal = a.totalScore ?? 0
        bVal = b.totalScore ?? 0
      } else if (sortBy === 'transparency') {
        aVal = a.transparencyScore ?? 0
        bVal = b.transparencyScore ?? 0
      } else if (sortBy === 'explainability') {
        aVal = a.explainabilityScore ?? 0
        bVal = b.explainabilityScore ?? 0
      } else if (sortBy === 'accountability') {
        aVal = a.accountabilityScore ?? 0
        bVal = b.accountabilityScore ?? 0
      } else {
        aVal = a[sortBy] ?? 0
        bVal = b[sortBy] ?? 0
      }
      
      return sortOrder === 'desc' ? bVal - aVal : aVal - bVal
    })

  const ScoreBar = ({ score, maxScore = 10, color = "blue" }) => (
    <div className="flex items-center gap-3">
      <div className="w-32 bg-gray-200 rounded-full h-3 relative overflow-hidden">
        <div 
          className={`h-full bg-gradient-to-r from-${color}-400 to-${color}-600 rounded-full transition-all duration-1000 ease-out`}
          style={{ width: `${((score ?? 0) / maxScore) * 100}%` }}
        />
      </div>
      <span className="text-sm font-semibold text-gray-700 min-w-[40px]">
        {(score ?? 0)}/{maxScore}
      </span>
    </div>
  )

  const RadarChart = ({ policy }) => {
    const metrics = [
      { name: 'Transparency', score: policy.transparency?.score ?? 0, max: 10 },
      { name: 'Explainability', score: policy.explainability?.score ?? 0, max: 10 },
      { name: 'Accountability', score: policy.accountability?.score ?? 0, max: 10 }
    ]
    const radius = 80
    const centerX = 100
    const centerY = 100
    const points = metrics.map((metric, index) => {
      const angle = (index * 120 - 90) * (Math.PI / 180)
      const distance = (metric.score / metric.max) * radius
      return {
        x: centerX + Math.cos(angle) * distance,
        y: centerY + Math.sin(angle) * distance
      }
    })
    const maxPoints = metrics.map((metric, index) => {
      const angle = (index * 120 - 90) * (Math.PI / 180)
      return {
        x: centerX + Math.cos(angle) * radius,
        y: centerY + Math.sin(angle) * radius
      }
    })
    return (
      <div className="flex justify-center">
        <svg width="200" height="200" className="overflow-visible">
          {/* Grid circles */}
          {[0.2, 0.4, 0.6, 0.8, 1].map((scale, i) => (
            <circle
              key={`circle-${scale}`}
              cx={centerX}
              cy={centerY}
              r={radius * scale}
              fill="none"
              stroke="#e5e7eb"
              strokeWidth="1"
            />
          ))}
          {/* Grid lines */}
          {maxPoints.map((point, index) => (
            <line
              key={`line-${index}`}
              x1={centerX}
              y1={centerY}
              x2={point.x}
              y2={point.y}
              stroke="#e5e7eb"
              strokeWidth="1"
            />
          ))}
          {/* Filled area */}
          <polygon
            points={points.map(p => `${p.x},${p.y}`).join(' ')}
            fill="rgba(59, 130, 246, 0.2)"
            stroke="rgb(59, 130, 246)"
            strokeWidth="2"
          />
          {/* Data points */}
          {points.map((point, index) => (
            <circle
              key={`point-${index}-${point.x}-${point.y}`}
              cx={point.x}
              cy={point.y}
              r="4"
              fill="rgb(59, 130, 246)"
            />
          ))}
          {/* Labels */}
          {metrics.map((metric, index) => {
            const angle = (index * 120 - 90) * (Math.PI / 180)
            const labelDistance = radius + 25
            const x = centerX + Math.cos(angle) * labelDistance
            const y = centerY + Math.sin(angle) * labelDistance
            return (
              <text
                key={`label-${metric.name}`}
                x={x}
                y={y}
                textAnchor="middle"
                dominantBaseline="middle"
                fontSize="12"
                fill="#374151"
                fontWeight="600"
              >
                {metric.name}
              </text>
            )
          })}
        </svg>
      </div>
    )
  }



  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-2xl font-bold text-blue-600">Loading policy data...</div>
      </div>
    )
  }

  // Debug info: show counts and unmatched policies
  const unmatchedPolicies = policyData.filter(p => {
    // Country not matched
    const matchedCountry = fullCountries.some(countryObj => {
      const countryName = typeof countryObj === 'string' ? countryObj : countryObj.name
      const countryCode = typeof countryObj === 'string' ? '' : (countryObj.code || countryObj.countryCode || '')
      return (
        (p.country && p.country.trim().toLowerCase() === countryName.trim().toLowerCase()) ||
        (countryCode && p.countryCode && p.countryCode.trim().toLowerCase() === countryCode.trim().toLowerCase())
      )
    })
    // Category not matched
    const matchedCategory = fullPolicyAreas.some(area => {
      return (
        (p.category && p.category.trim().toLowerCase() === area.name.trim().toLowerCase()) ||
        (area.id && p.categoryId && p.categoryId === area.id)
      )
    })
    return !matchedCountry || !matchedCategory
  })

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Debug Info */}
        <div className="mb-4">
          <div className="flex flex-wrap gap-6 items-center bg-white rounded-xl shadow p-4">
            <div className="text-blue-700 font-semibold">Total Policies: {policyData.length}</div>
            <div className="text-green-700 font-semibold">Total Countries: {fullCountries.length}</div>
            <div className="text-purple-700 font-semibold">Visible Countries: {countryData.length}</div>
            <div className="text-red-700 font-semibold">Unmatched Policies: {unmatchedPolicies.length}</div>
            {unmatchedPolicies.length > 0 && (
              <details className="text-xs text-red-600">
                <summary>Show unmatched policies</summary>
                <ul className="list-disc ml-4">
                  {unmatchedPolicies.map((p, i) => (
                    <li key={`unmatched-${p.id ?? p.name ?? i}-${p.country ?? 'unknown'}-${p.category ?? 'unknown'}`}>{p.name || p.policyName} ({p.country}, {p.category})</li>
                  ))}
                </ul>
              </details>
            )}
          </div>
        </div>
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              </div>
              <div>
                <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                  Policy Ranking System
                </h1>
                <p className="text-gray-600">
                  AI Policy Transparency, Explainability & Accountability Assessment
                </p>
              </div>
            </div>
            {setView && (
              <button
                onClick={() => setView('home')}
                className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-gray-100 to-gray-200 hover:from-gray-200 hover:to-gray-300 rounded-xl font-semibold text-gray-700 transition-all duration-300 hover:shadow-lg"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m0 0v-6a1 1 0 011-1h2a1 1 0 011 1v6m3 0a1 1 0 001-1V10M9 21h6" />
                </svg>
                Back to Home
              </button>
            )}
          </div>
        </div>

        {/* View Selector */}
        <div className="bg-white rounded-2xl shadow-lg p-1 mb-8 inline-flex">
          {[{ key: 'overview', label: 'Overview', icon: '📊' },
            { key: 'countries', label: 'Country Comparison', icon: '🌍' },
            { key: 'detailed', label: 'Detailed Analysis', icon: '🔍' },
            { key: 'methodology', label: 'Methodology', icon: '📋' }
          ].map(view => (
            <button
              key={`view-${view.key}`}
              onClick={() => setSelectedView(view.key)}
              className={`flex items-center gap-2 px-6 py-3 rounded-xl transition-all duration-300 ${
                selectedView === view.key
                  ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white shadow-lg'
                  : 'text-gray-600 hover:bg-gray-50'
              }`}
            >
              <span>{view.icon}</span>
              <span className="font-semibold">{view.label}</span>
            </button>
          ))}
        </div>

        {/* Overview View */}
        {selectedView === 'overview' && (
          <div className="space-y-6">
            {/* Filters and Sorting */}
            <div className="bg-white rounded-2xl shadow-lg p-6">
              <div className="flex flex-wrap gap-4 items-center">
                <div className="flex items-center gap-2">
                  <label className="text-sm font-semibold text-gray-700">Sort by:</label>
                  <select
                    value={sortBy}
                    onChange={(e) => setSortBy(e.target.value)}
                    className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="totalScore">Total Score</option>
                    <option value="transparency">Transparency</option>
                    <option value="explainability">Explainability</option>
                    <option value="accountability">Accountability</option>
                  </select>
                </div>
                
                <div className="flex items-center gap-2">
                  <label className="text-sm font-semibold text-gray-700">Order:</label>
                  <select
                    value={sortOrder}
                    onChange={(e) => setSortOrder(e.target.value)}
                    className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="desc">Highest First</option>
                    <option value="asc">Lowest First</option>
                  </select>
                </div>

                <div className="flex items-center gap-2">
                  <label className="text-sm font-semibold text-gray-700">Category:</label>
                  <select
                    value={filterCategory}
                    onChange={(e) => setFilterCategory(e.target.value)}
                    className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  >
                    {categoryObjects.map(cat => (
                      <option key={`cat-${cat.id}-${cat.name}`} value={cat.name}>
                        {cat.name}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            </div>

            {/* Rankings List */}
            <div className="grid gap-6">
              {sortedPolicies.map((policy, index) => {
                const policyKey = policy.id ?? policy.name ?? index;
                const isExpanded = !!expandedPolicies[policyKey];
                return (
                  <div
                    key={`policy-${policyKey}`}
                    className={`bg-white rounded-2xl shadow-lg transition-all duration-300 cursor-pointer ${isExpanded ? 'border-2 border-blue-400 p-6' : 'hover:shadow-xl p-6'}`}
                    onClick={() => setExpandedPolicies(prev => ({ ...prev, [policyKey]: !prev[policyKey] }))}
                  >
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center gap-4">
                        <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center text-white font-bold text-lg">
                          #{index + 1}
                        </div>
                        <div>
                          <h3 className="text-xl font-bold text-gray-800 flex items-center">
                            {policy.name}
                            {isExpanded && <span className="ml-2 text-blue-500">▼</span>}
                            {!isExpanded && <span className="ml-2 text-gray-400">▶</span>}
                          </h3>
                          <p className="text-gray-600">{policy.country} • {policy.year} • {policy.category}</p>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                          {policy.totalScore}/30
                        </div>
                        <div className="text-sm text-gray-500">Total Score</div>
                      </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                      <div className="space-y-2">
                        <div className="text-sm font-semibold text-gray-700">Transparency</div>
                        <ScoreBar score={policy.transparency?.score ?? 0} color="blue" />
                      </div>
                      <div className="space-y-2">
                        <div className="text-sm font-semibold text-gray-700">Explainability</div>
                        <ScoreBar score={policy.explainability?.score ?? 0} color="green" />
                      </div>
                      <div className="space-y-2">
                        <div className="text-sm font-semibold text-gray-700">Accountability</div>
                        <ScoreBar score={policy.accountability?.score ?? 0} color="purple" />
                      </div>
                    </div>

                    {isExpanded && (
                      <div className="mt-6 p-4 bg-gray-50 rounded-xl">
                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                          <div>
                            <h4 className="text-lg font-bold mb-4">Detailed Breakdown</h4>
                            <div className="space-y-4">
                              {Object.entries(evaluationCriteria).map(([category, questions]) => (
                                <div key={`breakdown-${category}-${policyKey}`} className="space-y-2">
                                  <h5 className="font-semibold text-gray-800 capitalize">{category}</h5>
                                  {questions.map((question, qIndex) => {
                                    const detailsArr = policy[category]?.details ?? [];
                                    const scoreVal = detailsArr[qIndex] ?? 0;
                                    return (
                                      <div key={`question-${category}-${policyKey}-${qIndex}`} className="flex items-center gap-2 text-sm">
                                          <li className="list-disc ml-6 text-gray-700">{question}</li>
                                      </div>
                                    );
                                  })}
                                </div>
                              ))}
                            </div>
                          </div>
                          <div>
                            <h4 className="text-lg font-bold mb-4">Visualization</h4>
                            <RadarChart policy={policy} />
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Country Comparison View */}
        {selectedView === 'countries' && (
          <div className="space-y-6">
            {/* Policy Area Selection */}
            <div className="bg-white rounded-2xl shadow-lg p-6">
              <h3 className="text-2xl font-bold mb-6 flex items-center gap-3">
                Select Policy Area for Country Comparison
              </h3>
              <p className="text-gray-600 mb-6">
                Click on a policy area to see countries ranked by their scores in that specific area.
              </p>
              
              {/* Policy Areas Selection Grid */}
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3 mb-4">
                {(() => {
                  // Get unique areas from actual data - policy_areas is an array
                  const allAreas = [];
                  policyData.forEach(policy => {
                    if (policy.policy_areas && Array.isArray(policy.policy_areas)) {
                      policy.policy_areas.forEach(area => {
                        if (area.area_name && !allAreas.includes(area.area_name)) {
                          allAreas.push(area.area_name);
                        }
                      });
                    }
                  });
                  
                  const categoriesToShow = allAreas.sort();
                  
                  if (categoriesToShow.length === 0) {
                    return <div className="col-span-full text-center text-gray-500">No policy areas found in database</div>;
                  }
                  
                  return categoriesToShow.map((area, index) => {
                    const areaIcons = ["🛡️", "🔒", "🎓", "🌐", "🎮", "📰", "💼", "🧠", "❤️", "📱", "⚖️", "🏛️", "🔐", "🌟", "💡"];
                    const areaColors = [
                      'from-red-500 to-pink-600', 'from-blue-500 to-cyan-600', 'from-green-500 to-emerald-600',
                      'from-purple-500 to-indigo-600', 'from-yellow-500 to-orange-600', 'from-gray-500 to-slate-600',
                      'from-teal-500 to-blue-600', 'from-pink-500 to-rose-600', 'from-emerald-500 to-green-600',
                      'from-indigo-500 to-purple-600', 'from-orange-500 to-red-600', 'from-cyan-500 to-teal-600',
                      'from-violet-500 to-purple-600', 'from-lime-500 to-green-600', 'from-amber-500 to-yellow-600'
                    ];
                    
                    // Get countries that have policies in this area
                    const areaCountries = [];
                    policyData.forEach(policy => {
                      if (policy.policy_areas && Array.isArray(policy.policy_areas)) {
                        const hasArea = policy.policy_areas.some(pArea => pArea.area_name === area);
                        if (hasArea && policy.country && !areaCountries.includes(policy.country)) {
                          areaCountries.push(policy.country);
                        }
                      }
                    });
                    
                    return (
                      <button
                        key={area}
                        onClick={() => setSelectedPolicyArea(area)}
                        className={`p-4 rounded-xl border-2 transition-all duration-200 ${
                          selectedPolicyArea === area 
                            ? `bg-gradient-to-r ${areaColors[index % areaColors.length]} border-transparent text-white shadow-lg` 
                            : 'bg-white border-gray-200 text-gray-700 hover:border-gray-300 hover:shadow-md'
                        }`}
                      >
                        <div className="text-2xl mb-2">{areaIcons[index % areaIcons.length]}</div>
                        <div className="font-semibold text-sm">{area}</div>
                        <div className="text-xs mt-1">
                          {areaCountries.length} countries
                        </div>
                        {selectedPolicyArea === area && (
                          <div className="mt-2 px-2 py-1 bg-white/20 rounded text-xs">
                            SELECTED
                          </div>
                        )}
                      </button>
                    );
                  });
                })()}
              </div>
            </div>

            {/* Country Comparison Bar Chart */}
            {selectedPolicyArea && (
              <div className="bg-white rounded-2xl shadow-lg p-6">
                <h3 className="text-2xl font-bold mb-6 flex items-center gap-3">
                  <span className="text-3xl">📊</span>
                  {selectedPolicyArea} - Country Comparison
                </h3>
                <p className="text-gray-600 mb-6">
                  Countries ranked by their average scores in <strong>{selectedPolicyArea}</strong> policies. 
                  Scores calculated from evaluation criteria: Transparency (0-10) + Explainability (0-10) + Accountability (0-10) = Total (0-30).
                </p>
                
                {(() => {
                  // Get countries that have policies in the selected area
                  const areaCountries = {};
                  
                  policyData.forEach(policy => {
                    if (policy.policy_areas && Array.isArray(policy.policy_areas)) {
                      const hasArea = policy.policy_areas.some(pArea => pArea.area_name === selectedPolicyArea);
                      if (hasArea && policy.country) {
                        if (!areaCountries[policy.country]) {
                          areaCountries[policy.country] = {
                            country: policy.country,
                            policies: [],
                            totalScore: 0,
                            transparencyScore: 0,
                            explainabilityScore: 0,
                            accountabilityScore: 0,
                            policyCount: 0
                          };
                        }
                        
                        // Use TEA scores directly from the policy
                        const policyTotalScore = policy.totalScore ?? 0;
                        const policyTransparencyScore = policy.transparencyScore ?? 0;
                        const policyExplainabilityScore = policy.explainabilityScore ?? 0;
                        const policyAccountabilityScore = policy.accountabilityScore ?? 0;
                        
                        areaCountries[policy.country].policies.push(policy);
                        areaCountries[policy.country].totalScore += policyTotalScore;
                        areaCountries[policy.country].transparencyScore += policyTransparencyScore;
                        areaCountries[policy.country].explainabilityScore += policyExplainabilityScore;
                        areaCountries[policy.country].accountabilityScore += policyAccountabilityScore;
                        areaCountries[policy.country].policyCount++;
                      }
                    }
                  });
                  
                  // Calculate averages and sort by score
                  const countryList = Object.values(areaCountries).map(country => ({
                    ...country,
                    avgTotalScore: country.policyCount > 0 ? country.totalScore / country.policyCount : 0,
                    avgTransparencyScore: country.policyCount > 0 ? country.transparencyScore / country.policyCount : 0,
                    avgExplainabilityScore: country.policyCount > 0 ? country.explainabilityScore / country.policyCount : 0,
                    avgAccountabilityScore: country.policyCount > 0 ? country.accountabilityScore / country.policyCount : 0,
                  })).sort((a, b) => b.avgTotalScore - a.avgTotalScore);
                  
                  if (countryList.length === 0) {
                    return (
                      <div className="text-center py-8">
                        <p className="text-gray-500 text-lg">No countries have policies in "{selectedPolicyArea}" area yet.</p>
                      </div>
                    );
                  }
                  
                  // Prepare chart data
                  const chartData = {
                    labels: countryList.map(c => c.country),
                    datasets: [
                      {
                        label: 'Average Total Score',
                        data: countryList.map(c => Math.round(c.avgTotalScore * 100) / 100),
                        backgroundColor: 'rgba(59, 130, 246, 0.8)',
                        borderColor: 'rgba(59, 130, 246, 1)',
                        borderWidth: 2,
                        borderRadius: 8,
                      }
                    ]
                  };
                  
                  const chartOptions = {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                      legend: {
                        display: false
                      },
                      tooltip: {
                        callbacks: {
                          afterLabel: function(context) {
                            const country = countryList[context.dataIndex];
                            return [
                              `Total Policies: ${country.policyCount}`,
                              `Transparency: ${Math.round(country.avgTransparencyScore * 100) / 100}/10`,
                              `Explainability: ${Math.round(country.avgExplainabilityScore * 100) / 100}/10`,
                              `Accountability: ${Math.round(country.avgAccountabilityScore * 100) / 100}/10`
                            ];
                          }
                        }
                      }
                    },
                    scales: {
                      y: {
                        beginAtZero: true,
                        max: 30,
                        title: {
                          display: true,
                          text: 'Average Score (out of 30)'
                        }
                      },
                      x: {
                        title: {
                          display: true,
                          text: 'Countries'
                        }
                      }
                    }
                  };
                  
                  return (
                    <div>
                      <div style={{ height: '400px' }}>
                        <Bar data={chartData} options={chartOptions} />
                      </div>
                      
                      {/* Country Details Table */}
                      <div className="mt-8">
                        <h4 className="text-lg font-semibold mb-4">Detailed Scores</h4>
                        <div className="overflow-x-auto">
                          <table className="w-full text-sm">
                            <thead>
                              <tr className="bg-gray-50">
                                <th className="text-left p-3 font-semibold">Rank</th>
                                <th className="text-left p-3 font-semibold">Country</th>
                                <th className="text-center p-3 font-semibold">Policies</th>
                                <th className="text-center p-3 font-semibold">Average Score</th>
                                <th className="text-center p-3 font-semibold">Transparency</th>
                                <th className="text-center p-3 font-semibold">Explainability</th>
                                <th className="text-center p-3 font-semibold">Accountability</th>
                              </tr>
                            </thead>
                            <tbody>
                              {countryList.map((country, index) => (
                                <tr key={country.country} className="border-b hover:bg-gray-50">
                                  <td className="p-3 font-semibold text-blue-600">#{index + 1}</td>
                                  <td className="p-3 font-medium">{country.country}</td>
                                  <td className="p-3 text-center">{country.policyCount}</td>
                                  <td className="p-3 text-center font-semibold">
                                    {Math.round(country.avgTotalScore * 100) / 100}/30
                                  </td>
                                  <td className="p-3 text-center">
                                    {Math.round(country.avgTransparencyScore * 100) / 100}/10
                                  </td>
                                  <td className="p-3 text-center">
                                    {Math.round(country.avgExplainabilityScore * 100) / 100}/10
                                  </td>
                                  <td className="p-3 text-center">
                                    {Math.round(country.avgAccountabilityScore * 100) / 100}/10
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </div>
                    </div>
                  );
                })()}
              </div>
            )}

            {/* Instructions when no policy area is selected */}
            {!selectedPolicyArea && (
              <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-2xl p-8 text-center">
                <div className="text-6xl mb-4">🎯</div>
                <h3 className="text-2xl font-bold text-gray-800 mb-2">Select a Policy Area</h3>
                <p className="text-gray-600 text-lg">
                  Choose any of the 10 policy areas above to see how countries compare in that specific area.
                </p>
                <p className="text-gray-500 text-sm mt-2">
                  Countries will be ranked by their average scores in the selected policy area.
                </p>
              </div>
            )}

            {/* Country Comparison Charts */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Bar Chart - Country Total Scores */}
              <div className="bg-white rounded-2xl shadow-lg p-6">
                <h3 className="text-xl font-bold mb-4">Average Total Scores by Country</h3>
                <div className="h-80">
                  <Bar
                    data={{
                      labels: countryData.map(c => c.country.length > 12 ? c.country.substring(0, 12) + '...' : c.country),
                      datasets: [
                        {
                          label: 'Average Total Score',
                          data: countryData.map(c => c.avgTotalScore.toFixed(1)),
                          backgroundColor: countryData.map((_, index) => {
                            const colors = [
                              'rgba(59, 130, 246, 0.8)',   // Blue
                              'rgba(34, 197, 94, 0.8)',    // Green
                              'rgba(168, 85, 247, 0.8)',   // Purple
                              'rgba(245, 158, 11, 0.8)',   // Orange
                              'rgba(239, 68, 68, 0.8)',    // Red
                              'rgba(20, 184, 166, 0.8)',   // Teal
                              'rgba(236, 72, 153, 0.8)',   // Pink
                              'rgba(139, 92, 246, 0.8)',   // Violet
                              'rgba(14, 165, 233, 0.8)',   // Sky
                              'rgba(16, 185, 129, 0.8)'    // Emerald
                            ]
                            return colors[index % colors.length]
                          }),
                          borderColor: countryData.map((_, index) => {
                            const colors = [
                              'rgba(59, 130, 246, 1)',
                              'rgba(34, 197, 94, 1)',
                              'rgba(168, 85, 247, 1)',
                              'rgba(245, 158, 11, 1)',
                              'rgba(239, 68, 68, 1)',
                              'rgba(20, 184, 166, 1)',
                              'rgba(236, 72, 153, 1)',
                              'rgba(139, 92, 246, 1)',
                              'rgba(14, 165, 233, 1)',
                              'rgba(16, 185, 129, 1)'
                            ]
                            return colors[index % colors.length]
                          }),
                          borderWidth: 2,
                          borderRadius: 8,
                          borderSkipped: false,
                        }
                      ]
                    }}
                    options={{
                      responsive: true,
                      maintainAspectRatio: false,
                      plugins: {
                        legend: {
                          display: false,
                        },
                        tooltip: {
                          callbacks: {
                            label: function(context) {
                              const country = countryData[context.dataIndex]
                              return [
                                `Average Score: ${context.parsed.y}/30`,
                                `Policies: ${country.totalPolicies}`,
                                `Transparency: ${country.avgTransparency.toFixed(1)}/10`,
                                `Explainability: ${country.avgExplainability.toFixed(1)}/10`,
                                `Accountability: ${country.avgAccountability.toFixed(1)}/10`
                              ]
                            }
                          }
                        }
                      },
                      scales: {
                        y: {
                          beginAtZero: true,
                          max: 30,
                          grid: {
                            color: 'rgba(0, 0, 0, 0.1)',
                          },
                          ticks: {
                            stepSize: 5
                          }
                        },
                        x: {
                          grid: {
                            display: false,
                          },
                          ticks: {
                            maxRotation: 45,
                            minRotation: 45
                          }
                        }
                      }
                    }}
                  />
                </div>
              </div>

              {/* Radar Chart - Top 6 Countries Comparison */}
              <div className="bg-white rounded-2xl shadow-lg p-6">
                <h3 className="text-xl font-bold mb-4">Top Countries - Dimension Comparison</h3>
                <div className="h-80">
                  <Radar
                    data={{
                      labels: ['Transparency', 'Explainability', 'Accountability'],
                      datasets: countryData.slice(0, 6).map((country, index) => ({
                        label: country.country.length > 12 ? country.country.substring(0, 12) + '...' : country.country,
                        data: [
                          country.avgTransparency,
                          country.avgExplainability,
                          country.avgAccountability
                        ],
                        borderColor: [
                          'rgba(59, 130, 246, 1)',
                          'rgba(34, 197, 94, 1)', 
                          'rgba(168, 85, 247, 1)',
                          'rgba(245, 158, 11, 1)',
                          'rgba(239, 68, 68, 1)',
                          'rgba(20, 184, 166, 1)'
                        ][index],
                        backgroundColor: [
                          'rgba(59, 130, 246, 0.2)',
                          'rgba(34, 197, 94, 0.2)',
                          'rgba(168, 85, 247, 0.2)',
                          'rgba(245, 158, 11, 0.2)',
                          'rgba(239, 68, 68, 0.2)',
                          'rgba(20, 184, 166, 0.2)'
                        ][index],
                        borderWidth: 2,
                        pointBackgroundColor: [
                          'rgba(59, 130, 246, 1)',
                          'rgba(34, 197, 94, 1)',
                          'rgba(168, 85, 247, 1)',
                          'rgba(245, 158, 11, 1)',
                          'rgba(239, 68, 68, 1)',
                          'rgba(20, 184, 166, 1)'
                        ][index],
                        pointBorderColor: '#fff',
                        pointHoverBackgroundColor: '#fff',
                        pointHoverBorderColor: [
                          'rgba(59, 130, 246, 1)',
                          'rgba(34, 197, 94, 1)',
                          'rgba(168, 85, 247, 1)',
                          'rgba(245, 158, 11, 1)',
                          'rgba(239, 68, 68, 1)',
                          'rgba(20, 184, 166, 1)'
                        ][index]
                      }))
                    }}
                    options={{
                      responsive: true,
                      maintainAspectRatio: false,
                      plugins: {
                        legend: {
                          position: 'bottom',
                        }
                      },
                      scales: {
                        r: {
                          angleLines: {
                            display: true
                          },
                          suggestedMin: 0,
                          suggestedMax: 10,
                          ticks: {
                            stepSize: 2
                          }
                        }
                      }
                    }}
                  />
                </div>
              </div>

              {/* Global Distribution */}
              <div className="bg-white rounded-2xl shadow-lg p-6">
                <h3 className="text-xl font-bold mb-4">Global Policy Distribution</h3>
                <div className="h-80">
                  <Doughnut
                    data={{
                      labels: countryData.map(c => c.country),
                      datasets: [
                        {
                          data: countryData.map(c => c.totalPolicies),
                          backgroundColor: countryData.map((_, index) => {
                            const colors = [
                              'rgba(59, 130, 246, 0.8)',
                              'rgba(34, 197, 94, 0.8)',
                              'rgba(168, 85, 247, 0.8)',
                              'rgba(245, 158, 11, 0.8)',
                              'rgba(239, 68, 68, 0.8)',
                              'rgba(20, 184, 166, 0.8)',
                              'rgba(236, 72, 153, 0.8)',
                              'rgba(139, 92, 246, 0.8)',
                              'rgba(14, 165, 233, 0.8)',
                              'rgba(16, 185, 129, 0.8)'
                            ]
                            return colors[index % colors.length]
                          }),
                          borderColor: countryData.map((_, index) => {
                            const colors = [
                              'rgba(59, 130, 246, 1)',
                              'rgba(34, 197, 94, 1)',
                              'rgba(168, 85, 247, 1)',
                              'rgba(245, 158, 11, 1)',
                              'rgba(239, 68, 68, 1)',
                              'rgba(20, 184, 166, 1)',
                              'rgba(236, 72, 153, 1)',
                              'rgba(139, 92, 246, 1)',
                              'rgba(14, 165, 233, 1)',
                              'rgba(16, 185, 129, 1)'
                            ]
                            return colors[index % colors.length]
                          }),
                          borderWidth: 2,
                        }
                      ]
                    }}
                    options={{
                      responsive: true,
                      maintainAspectRatio: false,
                      plugins: {
                        legend: {
                          position: 'bottom',
                        },
                        tooltip: {
                          callbacks: {
                            label: function(context) {
                              const country = countryData[context.dataIndex]
                              const total = context.dataset.data.reduce((a, b) => a + b, 0)
                              const percentage = ((context.parsed / total) * 100).toFixed(1)
                              return [
                                `${context.label}: ${context.parsed} policies (${percentage}%)`,
                                `Avg Score: ${country.avgTotalScore.toFixed(1)}/30`
                              ]
                            }
                          }
                        }
                      }
                    }}
                  />
                </div>
              </div>

              {/* Dimension Comparison Across All Countries */}
              <div className="bg-white rounded-2xl shadow-lg p-6">
                <h3 className="text-xl font-bold mb-4">Average Scores by Dimension</h3>
                <div className="h-80">
                  <Bar
                    data={{
                      labels: countryData.map(c => c.country.length > 8 ? c.country.substring(0, 8) + '...' : c.country),
                      datasets: [
                        {
                          label: 'Transparency',
                          data: countryData.map(c => c.avgTransparency.toFixed(1)),
                          backgroundColor: 'rgba(59, 130, 246, 0.8)',
                          borderColor: 'rgba(59, 130, 246, 1)',
                          borderWidth: 2,
                        },
                        {
                          label: 'Explainability',
                          data: countryData.map(c => c.avgExplainability.toFixed(1)),
                          backgroundColor: 'rgba(34, 197, 94, 0.8)',
                          borderColor: 'rgba(34, 197, 94, 1)',
                          borderWidth: 2,
                        },
                        {
                          label: 'Accountability',
                          data: countryData.map(c => c.avgAccountability.toFixed(1)),
                          backgroundColor: 'rgba(168, 85, 247, 0.8)',
                          borderColor: 'rgba(168, 85, 247, 1)',
                          borderWidth: 2,
                        }
                      ]
                    }}
                    options={{
                      responsive: true,
                      maintainAspectRatio: false,
                      plugins: {
                        legend: {
                          position: 'top',
                        }
                      },
                      scales: {
                        y: {
                          beginAtZero: true,
                          max: 10,
                          grid: {
                            color: 'rgba(0, 0, 0, 0.1)',
                          },
                          ticks: {
                            stepSize: 2
                          }
                        },
                        x: {
                          grid: {
                            display: false,
                          },
                          ticks: {
                            maxRotation: 45,
                            minRotation: 45
                          }
                        }
                      }
                    }}
                  />
                </div>
              </div>
            </div>

            {/* Key Insights */}
            <div className="bg-white rounded-2xl shadow-lg p-6">
              <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
                <span>💡</span>
                Key Insights
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                <div className="p-4 bg-blue-50 rounded-xl">
                  <h4 className="font-semibold text-blue-800 mb-2">🏆 Leading Country</h4>
                  <p className="text-blue-700">
                    <strong>{Array.isArray(countryData) && countryData[0] ? countryData[0].country : ''}</strong> leads with an average score of <strong>{Array.isArray(countryData) && countryData[0] ? countryData[0].avgTotalScore.toFixed(1) : ''}/30</strong>
                  </p>
                </div>
                <div className="p-4 bg-green-50 rounded-xl">
                  <h4 className="font-semibold text-green-800 mb-2">👁️ Best Transparency</h4>
                  <p className="text-green-700">
                    <strong>{Array.isArray(countryData) && countryData.length > 0 ? [...countryData].sort((a, b) => b.avgTransparency - a.avgTransparency)[0].country : ''}</strong> scores highest in transparency: <strong>{Array.isArray(countryData) && countryData.length > 0 ? [...countryData].sort((a, b) => b.avgTransparency - a.avgTransparency)[0].avgTransparency.toFixed(1) : ''}/10</strong>
                  </p>
                </div>
                <div className="p-4 bg-purple-50 rounded-xl">
                  <h4 className="font-semibold text-purple-800 mb-2">📊 Total Policies</h4>
                  <p className="text-purple-700">
                    <strong>{Array.isArray(policyData) ? policyData.length : 0}</strong> policies evaluated across <strong>{Array.isArray(countryData) ? countryData.length : 0}</strong> countries/regions
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Detailed Analysis View */}
        {selectedView === 'detailed' && (
          <div className="space-y-6">
            {/* Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
              {['transparency', 'explainability', 'accountability'].map((metric) => {
                const scores = policyData.map(p => p[metric]?.score ?? 0)
                const average = scores.reduce((a, b) => a + b, 0) / scores.length
                const max = Math.max(...scores)
                const min = Math.min(...scores)
                
                return (
                  <div key={metric} className="bg-white rounded-2xl shadow-lg p-6">
                    <div className="flex items-center gap-3 mb-4">
                      <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${
                        metric === 'transparency' ? 'bg-blue-100 text-blue-600' :
                        metric === 'explainability' ? 'bg-green-100 text-green-600' :
                        'bg-purple-100 text-purple-600'
                      }`}>
                        {metric === 'transparency' ? '👁️' : metric === 'explainability' ? '💡' : '⚖️'}
                      </div>
                      <h3 className="text-lg font-bold text-gray-800 capitalize">{metric}</h3>
                    </div>
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">Average:</span>
                        <span className="font-semibold">{average.toFixed(1)}/10</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">Highest:</span>
                        <span className="font-semibold">{max}/10</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">Lowest:</span>
                        <span className="font-semibold">{min}/10</span>
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>

            {/* Interactive Charts */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Bar Chart - Total Scores */}
              <div className="bg-white rounded-2xl shadow-lg p-6">
                <h3 className="text-xl font-bold mb-4">Total Scores Comparison</h3>
                <div className="h-80">
                  <Bar
                    data={{
                      labels: sortedPolicies.map(p => p.name.length > 20 ? p.name.substring(0, 20) + '...' : p.name),
                      datasets: [
                        {
                          label: 'Total Score',
                          data: sortedPolicies.map(p => p.totalScore),
                          backgroundColor: 'rgba(59, 130, 246, 0.8)',
                          borderColor: 'rgba(59, 130, 246, 1)',
                          borderWidth: 2,
                          borderRadius: 8,
                          borderSkipped: false,
                        }
                      ]
                    }}
                    options={{
                      responsive: true,
                      maintainAspectRatio: false,
                      plugins: {
                        legend: {
                          position: 'top',
                        },
                        title: {
                          display: false,
                        },
                        tooltip: {
                          callbacks: {
                            label: function(context) {
                              return `Total Score: ${context.parsed.y}/30`
                            }
                          }
                        }
                      },
                      scales: {
                        y: {
                          beginAtZero: true,
                          max: 30,
                          grid: {
                            color: 'rgba(0, 0, 0, 0.1)',
                          },
                          ticks: {
                            stepSize: 5
                          }
                        },
                        x: {
                          grid: {
                            display: false,
                          },
                          ticks: {
                            maxRotation: 45,
                            minRotation: 45
                          }
                        }
                      }
                    }}
                  />
                </div>
              </div>

              {/* Radar Chart - Metric Comparison */}
              <div className="bg-white rounded-2xl shadow-lg p-6">
                <h3 className="text-xl font-bold mb-4">Metrics Breakdown</h3>
                <div className="h-80">
                  <Radar
                    data={{
                      labels: ['Transparency', 'Explainability', 'Accountability'],
                      datasets: sortedPolicies.slice(0, 5).map((policy, index) => ({
                        label: policy.name.length > 15 ? policy.name.substring(0, 15) + '...' : policy.name,
                        data: [
                          policy.transparency?.score ?? 0,
                          policy.explainability?.score ?? 0,
                          policy.accountability?.score ?? 0
                        ],
                        borderColor: [
                          'rgba(59, 130, 246, 1)',
                          'rgba(34, 197, 94, 1)', 
                          'rgba(168, 85, 247, 1)',
                          'rgba(245, 158, 11, 1)',
                          'rgba(239, 68, 68, 1)'
                        ][index],
                        backgroundColor: [
                          'rgba(59, 130, 246, 0.2)',
                          'rgba(34, 197, 94, 0.2)',
                          'rgba(168, 85, 247, 0.2)',
                          'rgba(245, 158, 11, 0.2)',
                          'rgba(239, 68, 68, 0.2)'
                        ][index],
                        borderWidth: 2,
                        pointBackgroundColor: [
                          'rgba(59, 130, 246, 1)',
                          'rgba(34, 197, 94, 1)',
                          'rgba(168, 85, 247, 1)',
                          'rgba(245, 158, 11, 1)',
                          'rgba(239, 68, 68, 1)'
                        ][index],
                        pointBorderColor: '#fff',
                        pointHoverBackgroundColor: '#fff',
                        pointHoverBorderColor: [
                          'rgba(59, 130, 246, 1)',
                          'rgba(34, 197, 94, 1)',
                          'rgba(168, 85, 247, 1)',
                          'rgba(245, 158, 11, 1)',
                          'rgba(239, 68, 68, 1)'
                        ][index]
                      }))
                    }}
                    options={{
                      responsive: true,
                      maintainAspectRatio: false,
                      plugins: {
                        legend: {
                          position: 'bottom',
                        }
                      },
                      scales: {
                        r: {
                          angleLines: {
                            display: true
                          },
                          suggestedMin: 0,
                          suggestedMax: 10,
                          ticks: {
                            stepSize: 2
                          }
                        }
                      }
                    }}
                  />
                </div>
              </div>

              {/* Category Distribution Chart */}
              <div className="bg-white rounded-2xl shadow-lg p-6">
                <h3 className="text-xl font-bold mb-4">Policy Categories</h3>
                <div className="h-80">
                  <Doughnut
                    data={{
                      labels: fullPolicyAreas.map(a => a.name),
                      datasets: [
                        {
                          data: fullPolicyAreas.map(area => policyData.filter(p => p.category === area.name).length),
                          backgroundColor: [
                            'rgba(59, 130, 246, 0.8)',
                            'rgba(34, 197, 94, 0.8)',
                            'rgba(168, 85, 247, 0.8)',
                            'rgba(245, 158, 11, 0.8)',
                            'rgba(239, 68, 68, 0.8)',
                            'rgba(20, 184, 166, 0.8)',
                            'rgba(236, 72, 153, 0.8)',
                            'rgba(139, 92, 246, 0.8)',
                            'rgba(14, 165, 233, 0.8)',
                            'rgba(16, 185, 129, 0.8)'
                          ],
                          borderColor: [
                            'rgba(59, 130, 246, 1)',
                            'rgba(34, 197, 94, 1)',
                            'rgba(168, 85, 247, 1)',
                            'rgba(245, 158, 11, 1)',
                            'rgba(239, 68, 68, 1)',
                            'rgba(20, 184, 166, 1)',
                            'rgba(236, 72, 153, 1)',
                            'rgba(139, 92, 246, 1)',
                            'rgba(14, 165, 233, 1)',
                            'rgba(16, 185, 129, 1)'
                          ],
                          borderWidth: 2,
                        }
                      ]
                    }}
                    options={{
                      responsive: true,
                      maintainAspectRatio: false,
                      plugins: {
                        legend: {
                          position: 'bottom',
                        },
                        tooltip: {
                          callbacks: {
                            label: function(context) {
                              const total = context.dataset.data.reduce((a, b) => a + b, 0)
                              const percentage = ((context.parsed / total) * 100).toFixed(1)
                              return `${context.label}: ${context.parsed} policies (${percentage}%)`
                            }
                          }
                        }
                      }
                    }}
                  />
                </div>
              </div>

              {/* Score Distribution */}
              <div className="bg-white rounded-2xl shadow-lg p-6">
                <h3 className="text-xl font-bold mb-4">Score Distribution</h3>
                <div className="h-80">
                  <Bar
                    data={{
                      labels: ['Transparency', 'Explainability', 'Accountability'],
                      datasets: [
                        {
                          label: 'Average Score',
                          data: ['transparency', 'explainability', 'accountability'].map(metric => {
                            const scores = policyData.map(p => p[metric]?.score ?? 0)
                            return scores.length ? (scores.reduce((a, b) => a + b, 0) / scores.length).toFixed(1) : 0
                          }),
                          backgroundColor: [
                            'rgba(59, 130, 246, 0.8)',
                            'rgba(34, 197, 94, 0.8)', 
                            'rgba(168, 85, 247, 0.8)'
                          ],
                          borderColor: [
                            'rgba(59, 130, 246, 1)',
                            'rgba(34, 197, 94, 1)',
                            'rgba(168, 85, 247, 1)'
                          ],
                          borderWidth: 2,
                          borderRadius: 8,
                          borderSkipped: false,
                        }
                      ]
                    }}
                    options={{
                      responsive: true,
                      maintainAspectRatio: false,
                      plugins: {
                        legend: {
                          display: false,
                        }
                      },
                      scales: {
                        y: {
                          beginAtZero: true,
                          max: 10,
                          grid: {
                            color: 'rgba(0, 0, 0, 0.1)',
                          },
                          ticks: {
                            stepSize: 2
                          }
                        },
                        x: {
                          grid: {
                            display: false,
                          }
                        }
                      }
                    }}
                  />
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Methodology View */}
        {selectedView === 'methodology' && (
          <div className="bg-white rounded-2xl shadow-lg p-8">
            <h2 className="text-2xl font-bold mb-6">Evaluation Methodology</h2>
            
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
              {Object.entries(evaluationCriteria).map(([category, questions]) => (
                <div key={`methodology-${category}`} className="space-y-4">
                  <div className="flex items-center gap-3 mb-4">
                    <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${
                      category === 'transparency' ? 'bg-blue-100 text-blue-600' :
                      category === 'explainability' ? 'bg-green-100 text-green-600' :
                      'bg-purple-100 text-purple-600'
                    }`}>
                      {category === 'transparency' ? '👁️' : category === 'explainability' ? '💡' : '⚖️'}
                    </div>
                    <h3 className="text-xl font-bold text-gray-800 capitalize">{category} Score (0-10)</h3>
                  </div>
                  
                  <p className="text-gray-600 mb-4">
                    {category === 'transparency' && "Measures how open the policy is about its processes, decisions, data, and goals."}
                    {category === 'explainability' && "Measures how understandable the AI systems and decisions are to users and stakeholders."}
                    {category === 'accountability' && "Evaluates whether clear responsibilities, liabilities, and redress mechanisms are defined."}
                  </p>
                  
                  <div className="space-y-3">
                    <h4 className="font-semibold text-gray-800">Evaluation Questions:</h4>
                    {questions.map((question, index) => (
                      <div key={`methodology-question-${category}-${index}`} className="flex gap-3">
                        <div className="w-6 h-6 bg-gray-100 rounded-full flex items-center justify-center text-xs font-bold text-gray-600 flex-shrink-0 mt-0.5">
                          {index + 1}
                        </div>
                        <p className="text-sm text-gray-700">{question}</p>
                      </div>
                    ))}
                  </div>
                  
                  <div className="mt-4 p-4 bg-gray-50 rounded-lg">
                    <h5 className="font-semibold text-gray-800 mb-2">Scoring Guide:</h5>
                    <div className="space-y-1 text-sm">
                      <div className="flex items-center gap-2">
                        <div className="w-4 h-4 bg-green-500 rounded-full"></div>
                        <span>Yes/Fully = 2 points</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="w-4 h-4 bg-yellow-500 rounded-full"></div>
                        <span>Partial/Limited = 1 point</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="w-4 h-4 bg-red-500 rounded-full"></div>
                        <span>No = 0 points</span>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
            
            <div className="mt-8 p-6 bg-blue-50 rounded-xl">
              <h3 className="text-lg font-bold text-blue-800 mb-3">References</h3>
              <div className="space-y-2 text-sm text-blue-700">
                <p>• OECD AI Principles – Transparency & Accountability</p>
                <p>• OECD "Advancing Accountability in AI" (2023)</p>
                <p>• OECD AI Principles Implementation</p>
                <p>• Promoting equality in the use of Artificial Intelligence – an assessment framework for non-discriminatory AI</p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default PolicyRanking
