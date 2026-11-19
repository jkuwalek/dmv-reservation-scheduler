import { SlotBoard } from "./components/SlotBoard";
import { WatchForm } from "./components/WatchForm";

export default function Home() {
  return (
    <>
      <header className="masthead">
        <span className="wordmark">dmvwatch</span>
        <span className="coverage">New York only, for now</span>
      </header>

      <main className="page">
        <h1 className="lede">Every slot is taken. We watch for the one that isn&rsquo;t.</h1>

        <p className="standfirst">
          People cancel DMV reservations all day long. Those slots reappear for a few
          minutes and go to whoever happened to be looking. This checks for you instead.
        </p>

        <SlotBoard />

        <p className="formIntro">
          Give us the access code from your pre-screening email and we will tell you the
          moment something opens up at an office your code covers.
        </p>

        <WatchForm />

        <section className="afterword">
          <p>
            Your code is stored encrypted and used only to check your own eligibility. When
            you tell us you have booked, we delete it.
          </p>
          <p>
            Every alert has a link to stop the watching, and one to mute an office you are
            not willing to travel to.
          </p>
          <p>We never book anything for you. That part stays yours.</p>
        </section>
      </main>
    </>
  );
}
