import React from 'react';
import {
  SearchkitManager, SearchkitProvider, SearchBox, Hits, Layout, TopBar, LayoutBody, SideBar,
  HierarchicalMenuFilter, RefinementListFilter, ActionBar, LayoutResults, HitsStats, Panel,
  ActionBarRow, SelectedFilters, ResetFilters, NoHits, Pagination, InitialLoader, ExistsQuery, BoolMustNot
} from "searchkit";
import AntibodyHitsTable from './AntibodyHitsTable';
import { AdditionalColumns } from './AdditionalColumns';
import DownloadFile from './DownloadFile';
import Popup from 'reactjs-popup';
import { useCookies } from 'react-cookie';
import CookieConsent from 'react-cookie-consent';

const searchkit = new SearchkitManager("/");
searchkit.addDefaultQuery(query =>
  query.addQuery(
    BoolMustNot([ ExistsQuery("next_version_id") ])
  )
);

class BannerMessage extends React.Component {
    render () {
        if (!banner_message) {
            return(
              <div></div>
            );
        }

        return(
          <div className="banner">
            <div dangerouslySetInnerHTML={{ __html: banner_message }} />
          </div>
        );
    }
}

function collapseAllFilters() {
  const filters_dev = document.querySelectorAll(".sk-layout__filters");
  const header = filters_dev[0].querySelectorAll(".sk-panel__header.is-collapsable:not(.is-collapsed)")
  Array.prototype.forEach.call(header, function(f) {
    f.classList.add("is-collapsed");
  });
  const content = filters_dev[0].querySelectorAll(".sk-panel__content:not(.is-collapsed)")
  Array.prototype.forEach.call(content, function(c) {
    c.classList.add("is-collapsed");
  });
  //Array.prototype.forEach.call(filters_dev, function(h) {h.forceUpdate()});
  window.location.reload();
}

function Search(props) {
  const options = { showEllipsis: true, showLastIcon: false, showNumbers: true }
  //console.info('Search display: ', display);
  const [cookies] = useCookies([]);
  //console.info('Search cookies:', cookies);
  // cookies override the display defaults of the server
  for (const [key, value] of Object.entries(cookies)) {
    if (value==='true') {
      display[key] = "table-cell";
    }
  }
  //console.info('Search display after cookie set: ', display);

  return(
<SearchkitProvider searchkit={searchkit}>
  <>
  <CookieConsent>This website uses cookies to enhance the user experience.</CookieConsent>
  <Layout>
    <TopBar>
      <a href="https://portal.hubmapconsortium.org/">
        <svg align-items="center" height="45px"width="86px" viewBox="0 0 700 162" fill="#fff" aria-label="HubMAP Logo">
          <path d="M99.9.47v161.37H56.26V94.06H43.2v67.78H-.44V.47H43.2v57.71h13.06V.47H99.9zm112.16 29.1v132.26h-42.6l.73-10.99c-2.9 4.46-6.48 7.8-10.73 10.04-4.25 2.23-9.14 3.34-14.67 3.34-6.29 0-11.51-1.06-15.65-3.19-4.15-2.13-7.2-4.95-9.17-8.47-1.97-3.52-3.2-7.19-3.68-11.01-.48-3.82-.73-11.41-.73-22.77V29.57h41.88v90c0 10.3.33 16.41.98 18.34.66 1.93 2.44 2.89 5.34 2.89 3.11 0 4.96-1 5.55-2.99.59-1.99.88-8.41.88-19.24v-89h41.87zM228.33.47h43.54c13.75 0 24.17 1.03 31.25 3.09 7.08 2.06 12.8 6.23 17.15 12.5 4.35 6.28 6.53 16.38 6.53 30.33 0 9.43-1.54 16-4.61 19.72-3.08 3.72-9.14 6.57-18.19 8.57 10.09 2.19 16.93 5.83 20.53 10.92 3.59 5.09 5.39 12.88 5.39 23.39v14.96c0 10.91-1.3 18.98-3.89 24.23s-6.72 8.84-12.39 10.77c-5.67 1.93-17.28 2.89-34.83 2.89h-50.48V.47zm43.64 27.61v35.88c1.87-.07 3.32-.1 4.35-.1 4.28 0 7.01-1.01 8.19-3.04 1.17-2.03 1.76-7.82 1.76-17.39 0-5.05-.48-8.59-1.45-10.61-.97-2.03-2.23-3.3-3.78-3.84-1.56-.54-4.58-.83-9.07-.9zm0 61v45.15c6.15-.2 10.07-1.13 11.77-2.79 1.69-1.66 2.54-5.75 2.54-12.26v-15.05c0-6.91-.76-11.1-2.28-12.56-1.53-1.46-5.54-2.29-12.03-2.49zM480.22.47v161.37h-38.15l-.05-108.94-15.19 108.94h-27.06L383.76 55.39l-.05 106.45h-38.15V.47h56.47c1.68 9.7 3.4 21.14 5.18 34.31l6.2 41.05L423.44.48h56.78zm92.95 0l24.96 161.37h-44.6l-2.34-29h-15.61l-2.62 29h-45.12L510.1.47h63.07zm-23.13 103.76c-2.21-18.28-4.42-40.87-6.65-67.78-4.45 30.9-7.24 53.49-8.38 67.78h15.03zM605.54.47h43.95c11.88 0 21.03.9 27.42 2.69 6.39 1.79 11.19 4.39 14.41 7.77s5.39 7.49 6.53 12.31c1.14 4.82 1.71 12.28 1.71 22.38v14.05c0 10.3-1.11 17.81-3.32 22.53-2.21 4.72-6.27 8.34-12.18 10.86-5.91 2.53-13.63 3.79-23.17 3.79h-11.71v64.99h-43.64V.47zm43.64 27.61v41.06c1.24.07 2.31.1 3.21.1 4.01 0 6.79-.95 8.34-2.84 1.55-1.89 2.33-5.83 2.33-11.81V41.34c0-5.52-.9-9.1-2.7-10.76-1.78-1.67-5.52-2.5-11.18-2.5z"></path>
        </svg>
      </a>
     <div className='topmenuRight'>
        <a href="https://zenodo.org/doi/10.5281/zenodo.7418623" target='_blank' style={{display: "inline-block", color: "white", alignItems: "center", margin: "20px"}}>
          AVR SOP        
        </a>
        <a href="https://hubmapconsortium.org/open-working-groups" target='_blank' style={{display: "inline-block", color: "white", alignItems: "center", margin: "20px"}}>
          About AVRs at ARWG
        </a>
        <a href="/upload" style={{display: "inline-block", color: "white", alignItems: "center", margin: "20px"}}>
          Add AVRs
        </a>
      </div> 
    </TopBar>
    <BannerMessage />
    <LayoutBody>
      {/* <div className='panel'>
        <h2 >What is AVR? </h2>
        <p>Antibody Validation Reports (AVRs) provide information on the characterization of individual antibodies for multiplexed antibody-based imaging assays. AVRs additionally report details not included by antibody vendors such as the best performing conjugate for a particular clone and/or the impact of cycle order on immunogenicity. The current AVR database, on the Human Biomolecular Atlas Program (HuBMAP) AVR Search website, allows validated antibodies to be queried by clone, Research Resource Identifiers (RRIDs), catalog number, organ/tissue, and HuBMAP platform. This AVR metadata is included in a .CSV file uploaded to the portal by the contributing author for all AVRs submitted at one time. The AVR is completed as a text file and saved as a PDF for submission to the HuBMAP AVR upload site; it contains additional characterization data. Results from queries of the database may be downloaded as a .CSV and individual AVRs may be downloaded and viewed as a PDF.</p>
        <p>AVRs were piloted to provide individual antibody validation information for the diverse antibody-based methods employed by HuBMAP members. Importantly, AVRs have become tightly integrated with Organ Mapping Antibody Panels (OMAPs)(<a href="https://humanatlas.io/omap">https://humanatlas.io/omap</a>), a comprehensive panel of curated antibodies that identifies the major anatomical structures and cell types present in a specific organ. The selected antibodies are optimized for a tissue preservation method and multiplexed imaging modality. Both efforts share standardized metadata fields that will facilitate construction of a searchable antibody database. Beginning in 2023, we are excited to open AVR contributions to the larger community, beyond HuBMAP members.</p>
      </div> */}
   
      <h1 class="">Antibody Validation Report Search</h1>
      <SearchBox
      autofocus={true}
      queryOptions={{analyzer:"standard"}}
      searchOnChange={true}
      queryFields={[
          "antibody_uuid","antibody_hubmap_id","protocol_doi","manuscript_doi","uniprot_accession_number",
          "target_symbol","target_aliases","rrid","host",
          "clonality","clone_id","vendor","catalog_number","lot_number",
          "recombinant","organ","organ_uberon_id","omap_id","antigen_retrieval","hgnc_id","isotype",
          "concentration_value","dilution_factor","conjugate","method","tissue_preservation","cycle_number",
          "fluorescent_reporter","author_orcids","vendor_affiliation","created_by_user_displayname",
          "created_by_user_email","avr_pdf_filename", "previous_version_id", "next_version_id"
      ]}
      />
      <div className='searchView'>
      <SideBar>
        <h3>Filters</h3>
        <a className='collapseButton' onClick={collapseAllFilters}>Collapse all</a>
        <ResetFilters />
        <RefinementListFilter
          id="clonality"
          title="Clonality"
          field="clonality.keyword"
          operator="OR"
          searchable={true}
          size={10} limit={10}
          containerComponent={<Panel collapsable={true} defaultCollapsed={true}/>}
        />
        <RefinementListFilter
          id="conjugate"
          title="Conjugate"
          field="conjugate.keyword"
          operator="OR"
          searchable={true}
          size={10} limit={10}
          containerComponent={<Panel collapsable={true} defaultCollapsed={true}/>}
        />
        <RefinementListFilter
          id="host"
          title="Host"
          field="host.keyword"
          operator="OR"
          searchable={true}
          size={10} limit={10}
          containerComponent={<Panel collapsable={true} defaultCollapsed={true}/>}
        />
        <RefinementListFilter
          id="method"
          title="Method"
          field="method.keyword"
          operator="OR"
          searchable={true}
          size={10} limit={10}
          containerComponent={<Panel collapsable={true} defaultCollapsed={true}/>}
        />
        <RefinementListFilter
          id="organ"
          title="Organ"
          field="organ.keyword"
          operator="OR"
          searchable={true}
          size={10} limit={10}
          containerComponent={<Panel collapsable={true} defaultCollapsed={true}/>}
        />
        <RefinementListFilter
          id="recombinant"
          title="Recombinant"
          field="recombinant.keyword"
          operator="OR"
          searchable={true}
          size={10} limit={10}
          containerComponent={<Panel collapsable={true} defaultCollapsed={true}/>}
        />
        <RefinementListFilter
          id="target_symbol"
          title="Target Symbol"
          field="target_symbol.keyword"
          operator="OR"
          searchable={true}
          size={10} limit={10}
          containerComponent={<Panel collapsable={true} defaultCollapsed={true}/>}
        />
        <RefinementListFilter
          id="tissue_preservation"
          title="Tissue Preservation"
          field="tissue_preservation.keyword"
          operator="OR"
          searchable={true}
          size={10} limit={10}
          containerComponent={<Panel collapsable={true} defaultCollapsed={true}/>}
        />
        <RefinementListFilter
          id="vendor_name"
          title="Vendor"
          field="vendor_name.keyword"
          operator="OR"
          searchable={true}
          size={10} limit={10}
          containerComponent={<Panel collapsable={true} defaultCollapsed={true}/>}
        />

      </SideBar>

      <LayoutResults>

        <ActionBar>
          <ActionBarRow>
          <HitsStats />
          </ActionBarRow>
          <ActionBarRow>
            <SelectedFilters />
          </ActionBarRow>
        </ActionBar>

        <Popup trigger={<button className="button-placement">Configure Columns</button>}
              contentStyle={{width: "280px"}}
              modal>
          {close => (
              <div className="modal form-border">
                <button className="close" onClick={close}>
                  &times;
                </button>
                <AdditionalColumns/>
              </div>
          )}
        </Popup>

          <Hits
            listComponent={AntibodyHitsTable}
            hitsPerPage={20}
            mod="sk-hits-list"
          />
        <InitialLoader />
        <NoHits />

        <Pagination options={options} />
        <DownloadFile />

      </LayoutResults>
      </div>
    </LayoutBody>
  </Layout>
  </>
</SearchkitProvider>
)};

export default Search;
