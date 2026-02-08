import Image from "next/image";
import Button from "@/components/ui/Button";
import Card from "@/components/ui/Card";

export default function HomePage() {
  return (
    <main className="flex flex-col gap-24">

      {/* HERO */}
      <section className="container mx-auto px-6 pt-20 text-center">
        <h1 className="text-4xl md:text-6xl font-bold">
          Build modern dashboards faster
        </h1>
        <p className="mt-6 text-gray-600 max-w-2xl mx-auto">
          A clean Next.js + Tailwind UI system designed for rapid development.
        </p>

        <div className="mt-8 flex justify-center gap-4">
          <Button>Get Started</Button>
          <Button variant="outline">Live Demo</Button>
        </div>

        <div className="mt-12 flex justify-center">
          <Image
            src="/landing/hero.png"
            alt="Dashboard preview"
            width={900}
            height={500}
            className="rounded-xl shadow-lg"
          />
        </div>
      </section>

      {/* FEATURES */}
      <section className="container mx-auto px-6">
        <h2 className="text-3xl font-semibold text-center mb-12">
          Features
        </h2>

        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {["Fast", "Reusable", "Responsive"].map((feature) => (
            <Card key={feature} className="p-6 text-center">
              <h3 className="font-semibold text-lg">{feature}</h3>
              <p className="text-gray-600 mt-2">
                Built with scalability and clean UI patterns in mind.
              </p>
            </Card>
          ))}
        </div>
      </section>

      {/* TESTIMONIALS */}
      <section className="bg-gray-50 py-20">
        <div className="container mx-auto px-6">
          <h2 className="text-3xl font-semibold text-center mb-12">
            What users say
          </h2>

          <div className="grid gap-6 md:grid-cols-3">
            {[1, 2, 3].map((i) => (
              <Card key={i} className="p-6">
                <p className="text-gray-600">
                  “This UI kit saved us weeks of development time.”
                </p>

                <div className="flex items-center gap-3 mt-4">
                  <Image
                    src="/landing/avatar.png"
                    alt="User"
                    width={40}
                    height={40}
                    className="rounded-full"
                  />
                  <span className="font-medium">User {i}</span>
                </div>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* FOOTER */}
      <footer className="border-t py-6 text-center text-gray-500">
        © 2025 Acme UI. All rights reserved.
      </footer>

    </main>
  );
}
