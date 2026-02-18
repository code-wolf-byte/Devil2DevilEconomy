import { ASUHeader } from "@asu/component-header-footer";
import asuLogoVertical from "@asu/component-header-footer/dist/assets/img/arizona-state-university-logo-vertical.png";
import asuLogoHorizontal from "@asu/component-header-footer/dist/assets/img/arizona-state-university-logo.png";

export default function Header({ isAuthenticated = false }) {
    const logo = {
        alt: "Arizona State University",
        src: asuLogoVertical,
        mobileSrc: asuLogoHorizontal,
        brandLink: "https://asu.edu",
    };

    // partnerLogo is required by the type even if you’re not a partner.
    // If isPartner=false, it typically won’t render, but we still pass a safe value.
    const blankImg = "data:image/gif;base64,R0lGODlhAQABAAAAACw=";
    const partnerLogo = {
        alt: "Partner",
        src: blankImg,
        mobileSrc: blankImg,
        brandLink: "/",
    };

    const navTree = [
  {
    id: 0,
    href: "/",
    text: "Home",
    type: "link",
    class: "nav-home",
  },
  {
    id: 1,
    href: "/store",
    text: "Store",
  },
  {
    id: 2,
    href: "/how-to-earn",
    text: "How to Earn",
  },
  {
    id: 3,
    href: "/leaderboard",
    text: "Leaderboard",
  },
  ...(isAuthenticated ? [{
    id: 4,
    href: "/my-purchases",
    text: "My Purchases",
    type: "link",
  }] : []),
];


    return (
        <ASUHeader
            isPartner={false}
            navTree={navTree}
            mobileNavTree={navTree}
            title="Devil2Devil Rewards Shop"
            baseUrl="/"
            partnerLogo={partnerLogo}
            logo={logo}
            buttons={[]}
            breakpoint="Lg"
            animateTitle={false}
            expandOnHover={true}
            searchUrl="https://search.asu.edu/search"
            site="devil2devil-rewards-shop"
        />
    );
}
      
