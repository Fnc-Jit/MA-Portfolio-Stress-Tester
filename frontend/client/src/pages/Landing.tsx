import { Button } from "@/components/ui/button";
import { useLocation } from "wouter";
import { ArrowRight, TrendingUp, Zap, BarChart3, GitBranch } from "lucide-react";

export default function Landing() {
  const [, setLocation] = useLocation();

  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Navigation */}
      <nav className="border-b border-border/50 backdrop-blur-sm sticky top-0 z-50">
        <div className="container flex items-center justify-between h-16">
          <div className="text-xl font-bold text-accent">Portfolio Stress Tester</div>
          <a
            href="https://github.com"
            target="_blank"
            rel="noopener noreferrer"
            className="text-muted-foreground hover:text-accent transition-colors"
          >
            <GitBranch className="w-5 h-5" />
          </a>
        </div>
      </nav>

      {/* Hero Section with Animated Craft Elements */}
      <section className="relative overflow-hidden py-20 md:py-32">
        {/* Animated background craft elements */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          {/* Floating gradient orbs */}
          <div className="absolute top-10 left-10 w-72 h-72 bg-accent/10 rounded-full blur-3xl animate-pulse" />
          <div className="absolute bottom-10 right-10 w-96 h-96 bg-accent/5 rounded-full blur-3xl animate-pulse delay-1000" />
          
          {/* Animated lines */}
          <svg className="absolute inset-0 w-full h-full" preserveAspectRatio="none">
            <defs>
              <linearGradient id="lineGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="rgb(212, 175, 55)" stopOpacity="0.1" />
                <stop offset="100%" stopColor="rgb(212, 175, 55)" stopOpacity="0" />
              </linearGradient>
            </defs>
            <polyline
              points="0,100 250,50 500,100 750,30 1000,80"
              fill="none"
              stroke="url(#lineGradient)"
              strokeWidth="2"
              vectorEffect="non-scaling-stroke"
              className="animate-pulse"
            />
          </svg>
        </div>

        <div className="container relative z-10">
          <div className="max-w-3xl mx-auto text-center">
            <div className="mb-6 inline-block">
              <div className="px-4 py-2 rounded-full bg-accent/10 border border-accent/30 text-accent text-sm font-medium">
                Financial Risk Analysis
              </div>
            </div>

            <h1 className="text-5xl md:text-6xl font-bold mb-6 leading-tight">
              Stress-Test Your Portfolio
              <span className="block text-accent mt-2">Like a Bank Risk Desk</span>
            </h1>

            <p className="text-lg md:text-xl text-muted-foreground mb-8 leading-relaxed max-w-2xl mx-auto">
              Enter your portfolio. We run 4 independent risk models. Get a full risk report in seconds—the same methodology banks use, in your browser.
            </p>

            <div className="flex flex-col sm:flex-row gap-4 justify-center mb-12">
              <Button
                size="lg"
                className="bg-accent hover:bg-accent/90 text-accent-foreground font-semibold gap-2 group"
                onClick={() => setLocation("/dashboard")}
              >
                Get Started
                <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
              </Button>
              <Button
                size="lg"
                variant="outline"
                className="border-accent/50 hover:bg-accent/10"
                onClick={() => document.getElementById("how-it-works")?.scrollIntoView({ behavior: "smooth" })}
              >
                Learn More
              </Button>
            </div>

            {/* Animated stats */}
            <div className="grid grid-cols-3 gap-4 md:gap-8 pt-8 border-t border-border/30">
              <div className="text-center">
                <div className="numeric text-2xl md:text-3xl text-accent mb-1">4</div>
                <div className="text-sm text-muted-foreground">Risk Models</div>
              </div>
              <div className="text-center">
                <div className="numeric text-2xl md:text-3xl text-accent mb-1">&lt;1s</div>
                <div className="text-sm text-muted-foreground">Computation</div>
              </div>
              <div className="text-center">
                <div className="numeric text-2xl md:text-3xl text-accent mb-1">∞</div>
                <div className="text-sm text-muted-foreground">Portfolios</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section id="how-it-works" className="py-20 md:py-28 border-t border-border/30">
        <div className="container">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-bold mb-4">How It Works</h2>
            <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
              Three simple steps to understand your portfolio risk
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8 max-w-4xl mx-auto">
            {/* Step 1 */}
            <div className="relative">
              <div className="bg-card border border-border/50 rounded-lg p-8 h-full hover:border-accent/50 transition-colors">
                <div className="w-12 h-12 rounded-lg bg-accent/20 flex items-center justify-center mb-4">
                  <TrendingUp className="w-6 h-6 text-accent" />
                </div>
                <h3 className="text-xl font-semibold mb-3">Enter Your Portfolio</h3>
                <p className="text-muted-foreground">
                  Specify your stock tickers and portfolio weights. We validate everything in real-time.
                </p>
              </div>
              {/* Connector line */}
              <div className="hidden md:block absolute top-1/2 -right-4 w-8 h-0.5 bg-gradient-to-r from-accent/50 to-transparent" />
            </div>

            {/* Step 2 */}
            <div className="relative">
              <div className="bg-card border border-border/50 rounded-lg p-8 h-full hover:border-accent/50 transition-colors">
                <div className="w-12 h-12 rounded-lg bg-accent/20 flex items-center justify-center mb-4">
                  <Zap className="w-6 h-6 text-accent" />
                </div>
                <h3 className="text-xl font-semibold mb-3">Run 4 Risk Models</h3>
                <p className="text-muted-foreground">
                  Historical replay, parametric VaR, Monte Carlo simulation, and macro factor shocks—all at once.
                </p>
              </div>
              {/* Connector line */}
              <div className="hidden md:block absolute top-1/2 -right-4 w-8 h-0.5 bg-gradient-to-r from-accent/50 to-transparent" />
            </div>

            {/* Step 3 */}
            <div>
              <div className="bg-card border border-border/50 rounded-lg p-8 h-full hover:border-accent/50 transition-colors">
                <div className="w-12 h-12 rounded-lg bg-accent/20 flex items-center justify-center mb-4">
                  <BarChart3 className="w-6 h-6 text-accent" />
                </div>
                <h3 className="text-xl font-semibold mb-3">Get Full Risk Report</h3>
                <p className="text-muted-foreground">
                  Interactive charts, method comparison, and downloadable PDF—all in seconds.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Methodology Trust Section */}
      <section className="py-20 md:py-28 border-t border-border/30 bg-card/30">
        <div className="container">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-bold mb-4">Our Methodology</h2>
            <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
              Production-grade risk models used by financial institutions
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 max-w-6xl mx-auto">
            {/* Historical Replay */}
            <div className="bg-background border border-border/50 rounded-lg p-6 hover:border-accent/50 transition-colors group">
              <div className="w-10 h-10 rounded-lg bg-accent/20 flex items-center justify-center mb-4 group-hover:bg-accent/30 transition-colors">
                <BarChart3 className="w-5 h-5 text-accent" />
              </div>
              <h3 className="font-semibold mb-2">Historical Replay</h3>
              <p className="text-sm text-muted-foreground">
                Apply past crisis returns to your current portfolio and measure drawdowns.
              </p>
            </div>

            {/* Parametric VaR */}
            <div className="bg-background border border-border/50 rounded-lg p-6 hover:border-accent/50 transition-colors group">
              <div className="w-10 h-10 rounded-lg bg-accent/20 flex items-center justify-center mb-4 group-hover:bg-accent/30 transition-colors">
                <TrendingUp className="w-5 h-5 text-accent" />
              </div>
              <h3 className="font-semibold mb-2">Parametric VaR</h3>
              <p className="text-sm text-muted-foreground">
                Analytical Value-at-Risk using covariance matrix and normal distribution.
              </p>
            </div>

            {/* Monte Carlo */}
            <div className="bg-background border border-border/50 rounded-lg p-6 hover:border-accent/50 transition-colors group">
              <div className="w-10 h-10 rounded-lg bg-accent/20 flex items-center justify-center mb-4 group-hover:bg-accent/30 transition-colors">
                <Zap className="w-5 h-5 text-accent" />
              </div>
              <h3 className="font-semibold mb-2">Monte Carlo</h3>
              <p className="text-sm text-muted-foreground">
                Cholesky-decomposed correlated simulations with fat-tail sensitivity.
              </p>
            </div>

            {/* Factor Shock */}
            <div className="bg-background border border-border/50 rounded-lg p-6 hover:border-accent/50 transition-colors group">
              <div className="w-10 h-10 rounded-lg bg-accent/20 flex items-center justify-center mb-4 group-hover:bg-accent/30 transition-colors">
                <TrendingUp className="w-5 h-5 text-accent" />
              </div>
              <h3 className="font-semibold mb-2">Factor Shock</h3>
              <p className="text-sm text-muted-foreground">
                Macro factor exposure and hypothetical shock impact analysis.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 md:py-28 border-t border-border/30">
        <div className="container">
          <div className="max-w-3xl mx-auto text-center bg-card border border-accent/30 rounded-lg p-12">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">Ready to Stress-Test?</h2>
            <p className="text-lg text-muted-foreground mb-8">
              Start analyzing your portfolio risk in seconds. No sign-up required.
            </p>
            <Button
              size="lg"
              className="bg-accent hover:bg-accent/90 text-accent-foreground font-semibold gap-2 group"
              onClick={() => setLocation("/dashboard")}
            >
              Launch Dashboard
              <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
            </Button>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border/30 py-12 bg-card/50">
        <div className="container">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="text-muted-foreground text-sm">
              Built by Jitraj Esh
            </div>
            <a
              href="https://github.com"
              target="_blank"
              rel="noopener noreferrer"
              className="text-muted-foreground hover:text-accent transition-colors text-sm"
            >
              View on GitHub
            </a>
          </div>
        </div>
      </footer>

      {/* Animated delay utility for pulse */}
      <style>{`
        @keyframes pulse-delay {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
        }
        .delay-1000 {
          animation-delay: 1s;
        }
      `}</style>
    </div>
  );
}
