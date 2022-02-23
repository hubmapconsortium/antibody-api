import React from 'react';

import {
  SearchkitManager, SearchkitProvider, SearchBox, Hits,
  Layout, TopBar, LayoutBody, SideBar, HierarchicalMenuFilter,
  RefinementListFilter, ActionBar, LayoutResults, HitsStats,
  ActionBarRow, SelectedFilters, ResetFilters, NoHits, Pagination
} from "searchkit";

import AntibodyHitsTable from './AntibodyHitsTable';
import { Checkbox } from './Checkbox.js';

const searchkit = new SearchkitManager("/");
const options = { showEllipsis: true, showLastIcon: false, showNumbers: true }

const Search = () => (
  <SearchkitProvider searchkit={searchkit}>
  <Layout>
    <TopBar>
      <SearchBox
        autofocus={true}
        searchOnChange={true}
        prefixQueryFields={["antibody_name^3","target_name^2","host_organism", "vendor"]}/>
      <a href="/upload" style={{display: "flex", color: "white", alignItems: "center", margin: "20px"}}>UPLOAD</a>
    </TopBar>

    <LayoutBody>
      <SideBar>
        <HierarchicalMenuFilter
          fields={["target_name.keyword"]}
          title="Target Name"
          id="target_names"/>
        <HierarchicalMenuFilter
          fields={["vendor.keyword"]}
          title="Vendors"
          id="vendors"/>
        <RefinementListFilter
          id="host_organism"
          title="Host Organism"
          field="host_organism.keyword"
          operator="OR"
          size={10}/>
      </SideBar>
      <LayoutResults>
        <ActionBar>

          <ActionBarRow>
            <HitsStats/>
          </ActionBarRow>

          <ActionBarRow>
            <SelectedFilters/>
            <ResetFilters/>
          </ActionBarRow>

        </ActionBar>

        <table>
            <thead>
                <tr>
                    <td><b>Additional Columns:</b></td>
                    <td><Checkbox id_col="rrid_col" text_col="RRID"/></td>
                    <td><Checkbox id_col="clonality_col" text_col="Colonality"/></td>
                    <td><Checkbox id_col="catalog_number_col" text_col="Catalog#"/></td>
                    <td><Checkbox id_col="lot_number_col" text_col="Lot#"/></td>
                    <td><Checkbox id_col="vendor_col" text_col="Vendor"/></td>
                    <td><Checkbox id_col="recombinat_col" text_col="Recombinant"/></td>
                    <td><Checkbox id_col="ot_col" text_col="Organ/Tissue"/></td>
                    <td><Checkbox id_col="hp_col" text_col="Hubmap Platform"/></td>
                    <td><Checkbox id_col="so_col" text_col="Submitter Orcid"/></td>
                    <td><Checkbox id_col="email_col" text_col="Email"/></td>
                </tr>
            </thead>
        </table>

        <Hits mod="sk-hits-list"
          hitsPerPage={20}
          listComponent={AntibodyHitsTable}
          sourceFilter={["antibody_name", "host_organism", "uniprot_accession_number", "target_name", "rrid", "clonality", "catalog_number", "lot_number", "vendor", "recombinant", "organ_or_tissue", "hubmap_platform", "submitter_orciid", "created_by_user_email", "avr_filename", "avr_uuid"]}/>
        <NoHits/>

        <Pagination options={options}/>

      </LayoutResults>

    </LayoutBody>
  </Layout>
</SearchkitProvider>
);

export default Search;
