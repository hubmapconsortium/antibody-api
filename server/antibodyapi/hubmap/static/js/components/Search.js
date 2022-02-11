import React from 'react';

import {
  SearchkitManager, SearchkitProvider, SearchBox, Hits,
  Layout, TopBar, LayoutBody, SideBar, HierarchicalMenuFilter,
  RefinementListFilter, ActionBar, LayoutResults, HitsStats,
  ActionBarRow, SelectedFilters, ResetFilters, NoHits, Pagination
} from "searchkit";

import AntibodyHitsTable from './AntibodyHitsTable';

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
        <Hits mod="sk-hits-list"
          hitsPerPage={10}
          listComponent={AntibodyHitsTable}
          sourceFilter={["antibody_name", "target_name", "host_organism", "vendor"]}/>
        <NoHits/>
        <Pagination options={options}/>
      </LayoutResults>

    </LayoutBody>
  </Layout>
</SearchkitProvider>
);

export default Search;
