import React from "react";
import "@asu/unity-bootstrap-theme/dist/css/unity-bootstrap-theme.bundle.css";
import "@asu/unity-bootstrap-theme/dist/css/unity-bootstrap-header-footer.css";


const earnMethods = [
  {
    title: "Daily command",
    reward: "85 pitchforks per day",
    icon: "calendar-day",
    accent: "warning",
    body: (
      <>
        Use the <code>/daily</code> command once per day to claim your daily
        reward.
      </>
    ),
    meta: "Limit: 90 lifetime claims",
  },
  {
    title: "Admin reactions",
    reward: "Various rewards",
    icon: "thumbs-up",
    accent: "success",
    body: (
      <>
        Admins can react to your messages with special emojis to award points:
      </>
    ),
    list: [
      { label: "Campus photo", value: "100 pitchforks (one-time)" },
      { label: "Enrollment deposit", value: "500 pitchforks (one-time)" },
      { label: "Daily engagement", value: "25 pitchforks (max 3 per user)" },
    ],
  },
  {
    title: "Role bonuses",
    reward: "One-time rewards",
    icon: "crown",
    accent: "secondary",
    body: <>Earn bonus pitchforks when you receive certain Discord roles:</>,
    list: [
      { label: "Verification", value: "200 pitchforks" },
      { label: "Onboarding", value: "500 pitchforks" },
    ],
  },
  {
    title: "Birthday bonus",
    reward: "100 pitchforks",
    icon: "cake-candles",
    accent: "danger",
    body: (
      <>
        Set your birthday using <code>/birthday</code> to receive 100 pitchforks
        on your birthday each year.
      </>
    ),
  },
  {
    title: "Fill out survey",
    reward: "500 pitchforks",
    icon: "envelope",
    accent: "warning",
    body: (
      <>
        Complete the survey sent to your email to earn a one-time reward of 500
        pitchforks.
      </>
    ),
    meta: "One-time achievement",
  },
  {
    title: "Discord events",
    reward: "25 pitchforks each",
    icon: "calendar-check",
    accent: "primary",
    body: (
      <>
        Attend and participate in Discord events to earn 25 pitchforks per
        event.
      </>
    ),
    meta: "Per event participation",
  },
];

const tips = [
  {
    title: "Be active",
    body:
      "Engage regularly in the community to increase your chances of receiving admin reactions.",
  },
  {
    title: "Follow guidelines",
    body:
      "Make sure your content follows community guidelines to be eligible for rewards.",
  },
  {
    title: "Use the daily command",
    body:
      "Don’t forget to claim your daily reward every day to maximize your earnings.",
  },
  {
    title: "Check the leaderboard",
    body: (
      <>
        Use <code>/leaderboard</code> to see how you rank among other users.
      </>
    ),
  },
];

export default function HowToEarn() {
  return (
    <main id="main-content">
      {/* Page intro */}
      <section className="py-5">
        <div className="container-xl">
          <div className="mx-auto" style={{ maxWidth: 900 }}>
            <h1 className="display-5 fw-bold mb-3">How to earn pitchforks</h1>
            <p className="lead text-muted mb-0">
              Learn the ways you can earn pitchforks in the Devil2Devil economy.
            </p>
          </div>
        </div>
      </section>

      {/* Methods */}
      <section className="pb-5">
        <div className="container-xl">
          <div className="d-flex align-items-end justify-content-between flex-wrap gap-2 mb-4">
            <h2 className="h3 fw-bold mb-0">Ways to earn</h2>
            <p className="text-muted mb-0">
              Rewards may change over time based on community events.
            </p>
          </div>

          <div className="row g-4">
            {earnMethods.map((m) => (
              <div key={m.title} className="col-12 col-md-6">
                <div className="card h-100 shadow-sm">
                  <div className="card-body p-4">
                    <div className="d-flex align-items-start justify-content-between gap-3">
                      <div className="d-flex align-items-start gap-3">
                        {/* Icon badge */}
                        <div
                          className={`rounded-circle d-flex align-items-center justify-content-center bg-${m.accent} bg-opacity-10`}
                          style={{ width: 44, height: 44 }}
                          aria-hidden="true"
                        >
                          <i
                            className={`fa-solid fa-${m.icon} text-${m.accent}`}
                            aria-hidden="true"
                          />
                        </div>

                        <div>
                          <h3 className="h5 fw-bold mb-1">{m.title}</h3>
                          <div className={`small fw-semibold text-${m.accent}`}>
                            {m.reward}
                          </div>
                        </div>
                      </div>
                    </div>

                    <p className="text-muted mt-3 mb-0">{m.body}</p>

                    {m.list && (
                      <ul className="mt-3 mb-0 ps-3">
                        {m.list.map((li) => (
                          <li key={li.label} className="text-muted">
                            <span className="fw-semibold text-body">
                              {li.label}:
                            </span>{" "}
                            {li.value}
                          </li>
                        ))}
                      </ul>
                    )}

                    {m.meta && (
                      <div className="mt-3 small text-muted">{m.meta}</div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Tips */}
          <div className="card shadow-sm mt-5">
            <div className="card-body p-4 p-md-5">
              <h2 className="h4 fw-bold mb-4">Tips for earning more</h2>
              <div className="row g-4">
                {tips.map((t) => (
                  <div key={t.title} className="col-12 col-md-6">
                    <h3 className="h6 fw-bold mb-2">{t.title}</h3>
                    <p className="text-muted mb-0">{t.body}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Optional: ASU-style “note” */}
          <div className="alert alert-light border mt-4 mb-0" role="note">
            <span className="fw-semibold">Note:</span> If something looks off or
            you believe you missed a reward, contact a server admin.
          </div>
        </div>
      </section>
    </main>
  );
}
