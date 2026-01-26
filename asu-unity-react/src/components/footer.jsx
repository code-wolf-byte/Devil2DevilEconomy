import { ASUFooter } from "@asu/component-header-footer";
import asuLogoHorizontal from "@asu/component-header-footer/dist/assets/img/arizona-state-university-logo.png";

export default function Footer() {
    const logo = {
        alt: "Arizona State University",
        src: asuLogoHorizontal,
        brandLink: "https://asu.edu",
    };

    return (
        <ASUFooter
            logo={logo}
            baseUrl="/"
            site="devil2devil-economy"
            linksLeft={[
                {
                    href: "https://devil2devil.asu.edu/",
                    text: "About Devil2Devil",
                },
                
            ]}
            linksRight={[
                {
                    href: "https://www.asu.edu/terms-of-use",
                    text: "Terms of Use",
                },
                {
                    href: "https://www.asu.edu/privacy",
                    text: "Privacy",
                },
            ]}
        />
    );
}