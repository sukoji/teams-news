import { BrowserRouter, Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { AboutPage } from "./pages/AboutPage";
import { ArchivePage } from "./pages/ArchivePage";
import { DatePage } from "./pages/DatePage";
import { FeedPage } from "./pages/FeedPage";
import { HomePage } from "./pages/HomePage";
import { SearchPage } from "./pages/SearchPage";
import { SectionPage } from "./pages/SectionPage";
import { SourcePage } from "./pages/SourcePage";
import { SubscribePage } from "./pages/SubscribePage";

export default function App() {
  return (
    <BrowserRouter basename={import.meta.env.BASE_URL.replace(/\/$/, "")}>
      <Layout>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/feed" element={<FeedPage />} />
          <Route path="/search" element={<SearchPage />} />
          <Route path="/source/:slug" element={<SourcePage />} />
          <Route path="/section/:id" element={<SectionPage />} />
          <Route path="/archive" element={<ArchivePage />} />
          <Route path="/date/:date" element={<DatePage />} />
          <Route path="/subscribe" element={<SubscribePage />} />
          <Route path="/about" element={<AboutPage />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}
