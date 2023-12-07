import type { GetStaticProps, NextPage } from "next";
import { PROCESS_CRUMBS } from "src/constants/breadcrumbs";
import { ExternalRoutes } from "src/constants/routes";

import { Trans, useTranslation } from "next-i18next";
import { serverSideTranslations } from "next-i18next/serverSideTranslations";

import Breadcrumbs from "src/components/Breadcrumbs";
import PageSEO from "src/components/PageSEO";
import FullWidthAlert from "../components/FullWidthAlert";
import ProcessContent from "./content/ProcessContent";
import ProcessMethodology from "./content/ProcessMethodology";

const Process: NextPage = () => {
  const { t } = useTranslation("common", { keyPrefix: "Process" });

  return (
    <>
      <PageSEO title={t("page_title")} description={t("meta_description")} />
      <FullWidthAlert type="info" heading={t("alert_title")}>
        <Trans
          t={t}
          i18nKey="alert"
          components={{
            LinkToGrants: (
              <a
                target="_blank"
                rel="noopener noreferrer"
                href={ExternalRoutes.GRANTS_HOME}
              />
            ),
          }}
        />
      </FullWidthAlert>
      <Breadcrumbs breadcrumbList={PROCESS_CRUMBS} />
      <ProcessContent />
      <div className="padding-top-4 bg-gray-5">
        <ProcessMethodology />
      </div>
    </>
  );
};

// Change this to GetServerSideProps if you're using server-side rendering
export const getStaticProps: GetStaticProps = async ({ locale }) => {
  const translations = await serverSideTranslations(locale ?? "en");
  return { props: { ...translations } };
};

export default Process;
