import "@asu/unity-bootstrap-theme/dist/css/unity-bootstrap-theme.bundle.css";
import "@asu/unity-bootstrap-theme/dist/css/unity-bootstrap-header-footer.css";
import heroImage from "../assets/Hero.jpg";

const features = [
  {
    icon: "fa-coins",
    title: "Earn Pitchforks",
    description: "Use daily commands, participate in events, and hit milestones to earn pitchforks.",
    href: "/how-to-earn",
    label: "Learn how",
  },
  {
    icon: "fa-store",
    title: "Spend in the Store",
    description: "Browse rewards curated for the Devil2Devil community and redeem your pitchforks.",
    href: "/store",
    label: "Visit store",
  },
  {
    icon: "fa-ranking-star",
    title: "Climb the Leaderboard",
    description: "See how you rank among other users and compete for the top spot.",
    href: "/leaderboard",
    label: "View rankings",
  },
];

const quickStats = [
  { icon: "fa-terminal", label: "Daily Commands", detail: "Earn 85 pitchforks per day" },
  { icon: "fa-calendar-check", label: "Events", detail: "25 pitchforks per event" },
  { icon: "fa-gift", label: "Milestones", detail: "Up to 900 pitchforks" },
  { icon: "fa-star", label: "Bonuses", detail: "Surveys, boosts, and more" },
];

export default function Home() {
  return (
    <main id="main-content">
      <div className="uds-hero uds-hero-lg">
        <div className="hero-overlay" />
        <img
          className="hero"
          src={heroImage}
          alt="Devil2Devil Rewards Shop"
          loading="eager"
          decoding="async"
        />
        <h1>
          <span className="highlight-gold">Devil2Devil Economy</span>
        </h1>
        <div className="content text-white">
          <p>Earn pitchforks, unlock rewards, and engage with the ASU community.</p>
        </div>
        <a href="/store" className="btn btn-maroon">Browse Store</a>
      </div>

      
      {/* Features */}
      <section className="py-5 bg topo-white">
        <div className="container-xl">
          <div className="text-center mb-5">
            <h2 className="display-6 fw-bold">
              <span className="highlight-gold">How it works</span>
            </h2>
            <p className="lead text-muted">
              The Devil2Devil economy rewards active community members.
            </p>
          </div>

          <div className="row g-4">
            {features.map((feature) => (
              <div key={feature.title} className="col-12 col-md-4">
                <div className="border rounded bg-white p-4 h-100 text-center shadow-sm">
                  <div
                    className="bg-maroon rounded-circle d-inline-flex align-items-center justify-content-center mb-3"
                    style={{ width: 56, height: 56 }}
                  >
                    <i className={`fa-solid ${feature.icon} text-white fa-lg`} />
                  </div>
                  <h3 className="h5 fw-bold mb-2">{feature.title}</h3>
                  <p className="text-muted mb-3">{feature.description}</p>
                  <a href={feature.href} className="btn btn-maroon">{feature.label}</a>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>
    </main>
  );
}
