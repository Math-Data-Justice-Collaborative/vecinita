#!/usr/bin/env python3
"""
Test script demonstrating the HTML cleaner functionality.
"""

import sys
from pathlib import Path

from src.utils import HTMLCleaner

# Ensure src is on sys.path before importing
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


# Example from USCIS - mostly footer and boilerplate
USCIS_EXAMPLE = """
  </div></div>
      </div>

    <br><p>This office profile was last updated at 2023-07-07 08:16:42</p>
          </div>

                </div>



              <div class="reviewed-date">
    <div class="reviewed-date__label">Last Reviewed/Updated:</div>
                <div class="field field--name-field-display-date field__item"><time datetime="2025-04-10T23:26:06Z" class="datetime">04/10/2025</time>
</div>

  </div>

      </article>

      </div>

  </div>

                              </div>



                <div id="modal" class="modal page-modal"><div class="modal-content"><div class="modal-footer title-wrap"><div class="heading"><button id="modal-button" class="close" data-toggle="modal" data-dismiss="modal" aria-label="Close to proceed"><i class="fas fa-times" aria-labelledby="modal-button"></i></button><div class="modal-title" data-no-results="No results found." data-load-text="Loading..."></div></div></div><div class="modal-body"></div></div></div>
            </main>
          </div>
        </div>

              </div>
    </div>

  <div id="footer">

<div class="usa-footer-container">
  <footer class="usa-footer usa-footer--medium" role="contentinfo">
    <div class="grid-container usa-footer__return-to-top">
      <a href="#" class="focusable">Return to top</a>
    </div>

           <div class="usa-footer__primary-section">
         <div class="grid-container">
           <div class="grid-row grid-gap ">
                                         <div class="usa-footer__primary-section__menu ">
                 <nav class="usa-footer__nav" aria-label="Footer navigation">

                      <ul class="grid-row grid-gap menu" data-level="0">
                          <li class="menu__item mobile-lg:grid-col-4 desktop:grid-col-auto usa-footer__primary-content">
        <a href="/topics" class="nav__link usa-footer__primary-link" data-drupal-link-system-path="node/93148">Topics</a>
              </li>
                      <li class="menu__item mobile-lg:grid-col-4 desktop:grid-col-auto usa-footer__primary-content">
        <a href="/forms/forms" title="Forms" class="nav__link usa-footer__primary-link" data-drupal-link-system-path="node/88393">Forms</a>
              </li>
                      </ul>
                 </nav>
               </div>

                     </div>
                               </div>
       </div>

        <div class="usa-footer__intermediate-section">
          <div class="grid-container">

                      <div class="grid-row grid-gap">
              <div class="usa-footer__logo grid-row mobile-lg:grid-col-6 mobile-lg:grid-gap-2">
                <div class="mobile-lg:grid-col-auto">
                  <img class="usa-footer__logo-img" src="/sites/default/files/USCIS_Signature_Preferred_FC.png" alt="U.S. Department of Homeland Security Seal, U.S. Citizenship and Immigration Services">
              </div>
                              </div>

                <div class="usa-footer__contact-links mobile-lg:grid-col-6">
                  <div class="usa-footer__social-links grid-row grid-gap-1">
                                                                  <div class="grid-col-auto">
                          <a class="usa-social-link" href="https://www.facebook.com/uscis" >
                                                          <img
                                class="usa-social-link__icon"
                                src="/themes/contrib/dhs_uswds/img/social-icons/facebook.svg"
                                alt="Facebook" />
                                                      </a>
                        </div>
                                                                                                                                  <div class="grid-col-auto">
                          <a class="usa-social-link" href="https://www.twitter.com/uscis" >
                                                          <img
                              class="usa-social-link__icon"
                              src="/profiles/uscisd8_gov/themes/custom/uscis_design/assets/custom/images/x_no_circle.svg"
                              alt="X, formerly known as Twitter">
                                                      </a>
                        </div>
                      </div>

                                  <div class="usa-footer__contact-heading">
                                          <a class="usa-link" href="/about-us/contact-us" >Contact USCIS</a>
                                      </div>
                                  <address class="usa-footer__address">
                    <div class="usa-footer__contact-info grid-row grid-gap">
                                                                </div>
                  </address>
                </div>
                          </div>

          </div>
        </div>

    <div class="usa-footer__secondary-section">
      <div class="grid-container">
        <div class="grid-row grid-gap">
          <div class="grid-col-9">
            <section class="usa-identifier__section usa-identifier__section--masthead" aria-label="Agency identifier">
              <div class="usa-identifier__container">
                <div class="usa-identifier__logos">
                  <a href="https://www.dhs.gov" class="usa-identifier__logo">
                    <img class="usa-identifier__logo-img" src="/themes/contrib/dhs_uswds/logo.svg" alt="U.S. Department of Homeland Security Seal">
                  </a></div>
                <header class="visually-hidden">Agency description</header>
                <div class="usa-identifier__identity">
                  <p class="usa-identifier__identity-domain">USCIS.gov</p>
                  <p class="usa-identifier__identity-disclaimer">
                    An official website of the <a href="https://www.dhs.gov">U.S. Department of Homeland Security</a>
                  </p>
                </div>
              </div>
            </section>
          </div>
        </div>
      </div>
    </div>
  </footer>
</div>

  </div>

    <div class="region region-footer_third">
      <div id="block-qualtrics">


                      <div class="clearfix text-formatted field field--name-body field__item"><!--BEGIN QUALTRICS WEBSITE FEEDBACK SNIPPET--><script type="text/javascript">
(function(){var g=function(e,h,f,g){
this.get=function(a){for(var a=a+"=",c=document.cookie.split(";"),b=0,e=c.length;b<e;b++){for(var d=c[b];" "==d.charAt(0);)d=d.substring(1,d.length);if(0==d.indexOf(a))return d.substring(a.length,d.length)}return null};
this.set=function(a,c){var b="",b=new Date;b.setTime(b.getTime()+6048E5);b="; expires="+b.toGMTString();document.cookie=a+"="+c+b+"; path=/; "};
this.check=function(){var a=this.get(f);if(a)a=a.split(":");else if(100!=e)"v"==h&&(e=Math.random()>=e/100?0:100),a=[h,e,0],this.set(f,a.join(":"));else return!0;var c=a[1];if(100==c)return!0;switch(a[0]){case "v":return!1;case "r":return c=a[2]%Math.floor(100/c),a[2]++,this.set(f,a.join(":")),!c}return!0};
this.go=function(){if(this.check()){var a=document.createElement("script");a.type="text/javascript";a.src=g;document.body&&document.body.appendChild(a)}};
this.start=function(){var t=this;"complete"!==document.readyState?window.addEventListener?window.addEventListener("load",function(){t.go()},!1):window.attachEvent&&window.attachEvent("onload",function(){t.go()}):t.go()};};
try{(new g(100,"r","QSI_S_ZN_3WrTsyl9WWQdlxb","https://zn3wrtsyl9wwqdlxb-uscisomnichannel.gov1.siteintercept.qualtrics.com/SIE/?Q_ZID=ZN_3WrTsyl9WWQdlxb")).start()}catch(i){}})();
</script>
<div id="ZN_3WrTsyl9WWQdlxb"><!--DO NOT REMOVE-CONTENTS PLACED HERE--></div>
<!--END WEBSITE FEEDBACK SNIPPET--></div>

      </div>

  </div>

</div>

  </div>


    <script src="/core/assets/vendor/jquery/jquery.min.js?v=4.0.0-rc.1"></script>
"""


def test_html_cleaner():
    """Test the HTML cleaner with the provided example."""
    print("=" * 70)
    print("HTML CLEANER TEST")
    print("=" * 70)
    print("\n📋 Input: USCIS page footer HTML (645 lines of boilerplate)")
    print(f"   Input size: {len(USCIS_EXAMPLE)} characters\n")

    cleaned = HTMLCleaner.clean_html_to_text(USCIS_EXAMPLE)

    print("✅ Output after cleaning:")
    print("-" * 70)
    if cleaned:
        print(cleaned[:500])
        if len(cleaned) > 500:
            print(f"\n... (total {len(cleaned)} characters)")
    else:
        print("[EMPTY - All content was boilerplate/noise]")
    print("-" * 70)
    print(f"\n📊 Reduction: {len(USCIS_EXAMPLE)} → {len(cleaned)} characters")
    print(
        f"   Removed: {len(USCIS_EXAMPLE) - len(cleaned)} characters ({100 * (len(USCIS_EXAMPLE) - len(cleaned)) / len(USCIS_EXAMPLE):.1f}%)"
    )


if __name__ == "__main__":
    test_html_cleaner()
