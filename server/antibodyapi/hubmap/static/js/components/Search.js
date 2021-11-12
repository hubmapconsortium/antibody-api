import React from 'react';

import {
  SearchkitManager, SearchkitProvider, SearchBox, Hits,
  Layout, TopBar, LayoutBody, SideBar, HierarchicalMenuFilter,
  RefinementListFilter, ActionBar, LayoutResults, HitsStats,
  ActionBarRow, SelectedFilters, ResetFilters, NoHits
} from "searchkit";

import AntibodyHitsTable from './AntibodyHitsTable';

const searchkit = new SearchkitManager("/");

const Search = () => (
  <SearchkitProvider searchkit={searchkit}>
  <Layout>
    <TopBar>
      <SearchBox
        autofocus={true}
        searchOnChange={true}
        prefixQueryFields={["antibody_name^3","target_name^2","host_organism", "vendor"]}/>
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
        <Hits mod="sk-hits-list" hitsPerPage={50} listComponent={AntibodyHitsTable}
          sourceFilter={["antibody_name", "target_name", "host_organism", "vendor"]}/>
        <NoHits/>
      </LayoutResults>
    </LayoutBody>
  </Layout>
</SearchkitProvider>
);

export default Search;
