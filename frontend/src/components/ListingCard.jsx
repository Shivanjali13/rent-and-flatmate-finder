export default function ListingCard({ listing, onExpressInterest, interestSent }) {
  const score = listing.compatibility_score
  const scoreClass = score >= 80 ? 'score-high' : score >= 50 ? 'score-mid' : 'score-low'

  return (
    <div className="listing-card">
      {listing.photos?.[0] && (
        <img src={listing.photos[0]} alt={listing.location} className="listing-photo" />
      )}
      <div className="listing-body">
        <div className="listing-header">
          <h3>{listing.location}</h3>
          {score != null && (
            <span className={`score-badge ${scoreClass}`}>{score}/100</span>
          )}
        </div>
        <p className="rent">₹{listing.rent.toLocaleString('en-IN')}/month</p>
        <p>{listing.room_type} · {listing.furnishing_status}</p>
        <p>Available from {listing.available_from}</p>
        {listing.description && <p className="description">{listing.description}</p>}
        {listing.compatibility_explanation && (
          <p className="explanation">
            <strong>Why: </strong>{listing.compatibility_explanation}
            {listing.score_method === 'rule_based' && (
              <span className="method-tag"> (rule-based estimate)</span>
            )}
          </p>
        )}
        {onExpressInterest && (
          <button disabled={interestSent} onClick={() => onExpressInterest(listing.id)}>
            {interestSent ? 'Interest Sent' : 'Express Interest'}
          </button>
        )}
      </div>
    </div>
  )
}