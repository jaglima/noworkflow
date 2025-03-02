import {
  select as d3_select,
  Selection as d3_Selection,
  BaseType as d3_BaseType,
} from 'd3-selection';

import {Widget} from '@lumino/widgets';

import {json} from '@noworkflow/utils';

import {BaseActivationGraphWidget} from './base_activation_graph';

import {TrialGraph, TrialGraphData} from '@noworkflow/trial';


export
class TrialGraphWidget extends BaseActivationGraphWidget {

  name: string;
  cls: string;
  t1: string;
  t2: string;
  graph: TrialGraph;
  d3node: d3_Selection<d3_BaseType, {}, HTMLElement | null, any>;

  static url(trialId: string, selectedGraph: string, useCache: boolean) {
    let cache = useCache ? "1" : "0"
    return ("trials/"
      + trialId + "/" + selectedGraph + "/" + cache + ".json"
    );
  }

  constructor(name: string, cls: string, t1: string, t2: string) {
    super({ node: BaseActivationGraphWidget.createNode(cls) });
    this.d3node = d3_select(this.node);
    this.d3node.select('.reload-button')
      .on("click", () => {
        this.load(
          this.d3node.select(".graph-type").property("value"),
          this.d3node.select(".use-cache").property("checked"),
        )
      })
    this.addClass('content');
    this.addClass('trial-widget');
    this.title.label = name;
    this.title.closable = true;
    this.title.caption = `${name} Graph`;
    this.name = name;
    this.cls = cls;
    this.t1 = t1;
    this.t2 = t2;
  }

  setGraph(data: TrialGraphData, config: any={}) {
    let sub = this.node.getElementsByClassName("sub-content")[0];
    sub.innerHTML = "";
    this.graph = new TrialGraph(this.cls, sub, config);
    this.graph.load(data, this.t1, this.t2);

  }

  graphDefinition(selectedGraph: string = "namespace_match", useCache: boolean = true, genDataflow: boolean = true, data: TrialGraphData) {
    var result = super.graphDefinition(selectedGraph, useCache, genDataflow, data);
    return Object.assign({}, result, {
      queryTooltip: true
    });
  }

  load(selectedGraph: string = "namespace_match", useCache: boolean = true) {
    let sub = this.node.getElementsByClassName("sub-content")[0];
    json("Trial", sub, TrialGraphWidget.url(this.t1, selectedGraph, useCache), (data: TrialGraphData) => {
      this.configureGraph(selectedGraph, useCache, true, data);
    })
  }

  protected onResize(msg: Widget.ResizeMessage): void {
    if (this.graph) {
      this.graph.config.width = this.node.getBoundingClientRect().width - 24;
      this.graph.config.height = this.node.getBoundingClientRect().height - 24;
      this.graph.updateWindow();
    }
  }

}

