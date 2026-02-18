import "@asu/unity-bootstrap-theme/dist/css/unity-bootstrap-theme.bundle.css";
import "@asu/unity-bootstrap-theme/dist/css/unity-bootstrap-header-footer.css";
import heroImage from "../assets/Hero.jpg";

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

      
      <section className="py-5 bg topo-white">
        <div className="container">
          <div className="row align-items-center">
            <div className="col-12 col-sm-4 col-md-4 col-lg-4 mb-4 mb-md-0">
              <img
                className="img-fluid"
                src="/Devil2Devil.png"
                alt="Devil2Devil Discord"
                loading="lazy"
              />
            </div>
            <div className="col-12 col-sm-8 col-md-8 col-lg-8">
              <div className="uds-highlighted-heading">
                <h2><span className="highlight-gold">Devil2Devil Rewards Shop</span></h2>
              </div>
              <p>
                The Devil2Devil Rewards Shop is the official economy for the Devil2Devil Discord
                community. Earn pitchforks by staying active — check in daily, attend events,
                hit milestones, and participate in community challenges. Every action you take
                in the server adds up, putting you closer to rewards curated exclusively for
                Future Sun Devils.
              </p>
              <p>
                Once you've stacked your pitchforks, head to the store to redeem them for
                exclusive merchandise, Discord roles, digital items, and more. Check the
                leaderboard to see how you rank against your fellow Sun Devils and keep
                climbing to the top.
              </p>
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}
