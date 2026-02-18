import { useRef } from "react";

export default function EarnCarousel({ items }) {
  const scrollRef = useRef(null);

  const scroll = (direction) => {
    if (!scrollRef.current) return;
    const amount = 320;
    scrollRef.current.scrollBy({
      left: direction === "left" ? -amount : amount,
      behavior: "smooth",
    });
  };

  return (
    <div>
      <div
        ref={scrollRef}
        className="d-flex gap-3 overflow-auto pb-3 align-items-stretch"
        style={{ scrollSnapType: "x mandatory", scrollbarWidth: "none", msOverflowStyle: "none" }}
      >
        {items.map((item, i) => (
          <div
            key={`${item.action}-${item.description}-${i}`}
            className="card shadow-sm flex-shrink-0"
            style={{ width: 290, minHeight: 160, scrollSnapAlign: "start" }}
          >
            <div className="card-body p-3 d-flex flex-column h-100">
              <div className="d-flex align-items-center justify-content-between mb-2">
                <span className="badge bg-dark">{item.category}</span>
                <span className="fw-bold text-warning">{item.reward} <img src="/static/Coin_Gold.png" alt="pitchforks" style={{ width: 16, height: 16 }} /></span>
              </div>
              <h3 className="h6 fw-bold mb-1">{item.action}</h3>
              <p className="text-muted small mb-0 flex-grow-1">{item.description}</p>
            </div>
          </div>
        ))}
      </div>

      <div className="d-none d-md-flex justify-content-center gap-2 mt-3">
        <button
          className="btn btn-maroon rounded-circle d-flex align-items-center justify-content-center shadow"
          style={{ width: 44, height: 44 }}
          onClick={() => scroll("left")}
          aria-label="Scroll left"
        >
          <i className="fas fa-chevron-left text-white" aria-hidden="true" />
        </button>
        <button
          className="btn btn-maroon rounded-circle d-flex align-items-center justify-content-center shadow"
          style={{ width: 44, height: 44 }}
          onClick={() => scroll("right")}
          aria-label="Scroll right"
        >
          <i className="fas fa-chevron-right text-white" aria-hidden="true" />
        </button>
      </div>
    </div>
  );
}
