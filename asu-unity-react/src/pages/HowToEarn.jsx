import { useState } from "react";
import "@asu/unity-bootstrap-theme/dist/css/unity-bootstrap-theme.bundle.css";
import "@asu/unity-bootstrap-theme/dist/css/unity-bootstrap-header-footer.css";
import { Hero } from "@asu/unity-react-core";
import heroImage from "../assets/Hero.jpg";
import EarnCarousel from "../components/EarnCarousel";

const earnItems = [
  // Commands
  { action: "Daily check-in", description: 'Get points for checking in daily! Type "/daily" into any chat.', reward: "85 per day", category: "Commands" },
  { action: "Set Birthday", description: 'Type "/birthday" into any chat to set your birthdate.', reward: "50", category: "Commands" },
  { action: "Birthday celebration", description: "Earn points automatically on your birthday.", reward: "100", category: "Commands" },

  // Participation
  { action: "Events", description: "Attend an event in Devil2Devil in the Stage channel.", reward: "25 per event", category: "Participation" },
  { action: "Daily question", description: "Answer the question of the day in #general chat.", reward: "25 per day", category: "Participation" },
  { action: "Campus Photo", description: "Post a photo on campus in #proof-for-pitchforks.", reward: "100", category: "Participation" },
  { action: "Minecraft", description: "Win a Minecraft build challenge.", reward: "500", category: "Participation" },
  { action: "Minecraft", description: "Get second place in a Minecraft build challenge.", reward: "300", category: "Participation" },
  { action: "Minecraft", description: "Get third place in a Minecraft build challenge.", reward: "150", category: "Participation" },
  { action: "Minecraft", description: "Participate in a Minecraft build challenge.", reward: "25", category: "Participation" },

  // Milestones
  { action: "Onboarding", description: "Complete onboarding before joining the server.", reward: "100", category: "Milestones" },
  { action: "Verify", description: "Verify your admittance to ASU in #verify-here.", reward: "300", category: "Milestones" },
  { action: "Message", description: "Send your first message in any chat.", reward: "200", category: "Milestones" },
  { action: "Deposit", description: "Submit your enrollment deposit.", reward: "500", category: "Milestones" },
  { action: "React", description: "Add 10 reactions to messages.", reward: "200", category: "Milestones" },
  { action: "Voice chat", description: "Spend 60 minutes in the voice channels.", reward: "200", category: "Milestones" },
  { action: "Message", description: "Reach 100 total messages sent.", reward: "300", category: "Milestones" },
  { action: "Message", description: "Reach 1,000 total messages sent.", reward: "500", category: "Milestones" },
  { action: "React", description: "Add 500 reactions to messages.", reward: "500", category: "Milestones" },
  { action: "Voice chat", description: "Spend 720 minutes in the voice channels.", reward: "500", category: "Milestones" },
  { action: "Voice chat", description: "Spend 1,440 minutes in the voice channels.", reward: "700", category: "Milestones" },
  { action: "Message", description: "Reach 100,000 total messages sent.", reward: "900", category: "Milestones" },

  // Bonus
  { action: "Survey", description: "Fill out the survey via email or in #survey.", reward: "500", category: "Bonus" },
  { action: "Boost", description: "Boost the server.", reward: "500", category: "Bonus" },
  { action: "Instagram engagement", description: "Future Sun Devils new Instagram post gets 400 likes.", reward: "200 per post", category: "Bonus" },
];

const categories = ["All", "Commands", "Participation", "Milestones", "Bonus"];

export default function HowToEarn() {
  const [activeTab, setActiveTab] = useState("All");

  const filtered =
    activeTab === "All"
      ? earnItems
      : earnItems.filter((item) => item.category === activeTab);

  return (
    <main id="main-content">
      <Hero
        type="heading-hero"
        image={{
          url: heroImage,
          altText: "How to earn pitchforks",
          size: "large",
        }}
        title={{
          text: "How to earn pitchforks",
          highlightColor: "gold",
        }}
        contents={[
          { text: "Learn the ways you can earn pitchforks in the Devil2Devil economy." },
        ]}
        contentsColor="white"
      />

      <section className="py-5 bg topo-white" style={{ backgroundColor: "#191919" }}>
        <div className="uds-image-overlap content-left">
          <img src="/overlap.jpg" alt="Devil2Devil community at ASU" />
          <div className="content-wrapper">
            <h2>
              <span style={{
                background: "#ffc627",
                boxShadow: "-0.15em 0 0 #ffc627, 0.15em 0 0 #ffc627",
                color: "#191919",
              }}>
                Quick Start
              </span>
            </h2>
            <h3 className="h5 fw-bold mt-3 mb-2">Easiest Ways to Earn</h3>
            <p>Follow these three simple steps to start earning pitchforks today!</p>
            <p className="mb-0">Most rewards are automatic — just show up and participate.</p>
          </div>
        </div>
      </section>

      <section className="py-5 bg topo-white">
        <div className="container-xl">
          <div className="d-flex align-items-end justify-content-between flex-wrap gap-2 mb-4">
            <h2 className="h3 fw-bold mb-0">Ways to earn</h2>
            <p className="text-muted mb-0">
              Rewards may change over time based on community events.
            </p>
          </div>

          <div className="uds-tabbed-panels mb-4">
            <ul className="nav nav-tabs" role="tablist">
              {categories.map((cat) => (
                <li key={cat} className="nav-item" role="presentation">
                  <button
                    className={`nav-link ${activeTab === cat ? "active" : ""}`}
                    onClick={() => setActiveTab(cat)}
                    role="tab"
                    aria-selected={activeTab === cat}
                  >
                    {cat}
                  </button>
                </li>
              ))}
            </ul>
          </div>

          <EarnCarousel items={filtered} />

          <div className="alert alert-light border mt-5 mb-0" role="note">
            <span className="fw-semibold">Note:</span> If something looks off or
            you believe you missed a reward, contact a server admin.
          </div>
        </div>
      </section>
    </main>
  );
}
